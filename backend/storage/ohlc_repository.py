"""
Repository for OHLC data database operations
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session
from loguru import logger

from backend.storage.models import OHLC
from backend.storage.database import get_db_session


class OHLCRepository:
    """
    Data access layer for OHLC data operations

    Handles:
    - Batch inserts for OHLC bars
    - Queries by symbol, timeframe and time range
    - OHLC data aggregation and statistics
    """

    @staticmethod
    def insert_batch(records: List[Dict], session: Optional[Session] = None) -> int:
        """
        Insert multiple OHLC records in a single transaction

        Args:
            records: List of OHLC data dictionaries
            session: Optional database session (creates new if None)

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        use_context = session is None

        try:
            if use_context:
                with get_db_session() as db:
                    return OHLCRepository._do_insert(records, db)
            else:
                return OHLCRepository._do_insert(records, session)

        except Exception as e:
            logger.error(f"Error inserting OHLC data batch: {e}")
            raise

    @staticmethod
    def _do_insert(records: List[Dict], db: Session) -> int:
        """
        Internal method to perform batch insert

        Args:
            records: List of dictionaries with OHLC data
            db: Database session

        Returns:
            Number of records inserted
        """
        ohlc_objects = []

        for record in records:
            ohlc = OHLC(
                timestamp=record["timestamp"],
                symbol=record["symbol"],
                timeframe=record["timeframe"],
                open=record["open"],
                high=record["high"],
                low=record["low"],
                close=record["close"],
                volume=record["volume"],
                trade_count=record.get("trade_count", 0),
                vwap=record.get("vwap", None)
            )
            ohlc_objects.append(ohlc)

        db.add_all(ohlc_objects)
        db.commit()

        logger.debug(f"Inserted {len(ohlc_objects)} OHLC records")
        return len(ohlc_objects)

    @staticmethod
    def upsert_ohlc(record: Dict, session: Optional[Session] = None) -> bool:
        """
        Insert or update a single OHLC record

        Args:
            record: OHLC data dictionary
            session: Optional database session

        Returns:
            True if successful
        """
        try:
            if session:
                return OHLCRepository._do_upsert(record, session)
            else:
                with get_db_session() as db:
                    return OHLCRepository._do_upsert(record, db)
        except Exception as e:
            logger.error(f"Error upserting OHLC record: {e}")
            return False

    @staticmethod
    def _do_upsert(record: Dict, db: Session) -> bool:
        """Internal upsert logic"""
        # Check if record exists
        existing = db.query(OHLC).filter(
            and_(
                OHLC.symbol == record["symbol"],
                OHLC.timeframe == record["timeframe"],
                OHLC.timestamp == record["timestamp"]
            )
        ).first()

        if existing:
            # Update existing record
            existing.open = record["open"]
            existing.high = record["high"]
            existing.low = record["low"]
            existing.close = record["close"]
            existing.volume = record["volume"]
            existing.trade_count = record.get("trade_count", existing.trade_count)
            existing.vwap = record.get("vwap", existing.vwap)
        else:
            # Insert new record
            ohlc = OHLC(**record)
            db.add(ohlc)

        db.commit()
        return True

    @staticmethod
    def get_recent_ohlc(
        symbol: str,
        timeframe: str,
        limit: int = 100,
        session: Optional[Session] = None
    ) -> List[Dict]:
        """
        Get most recent OHLC data for a symbol and timeframe

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (1s, 1m, 5m)
            limit: Maximum number of records to return
            session: Optional database session

        Returns:
            List of OHLC data dictionaries
        """
        try:
            if session:
                ohlc_bars = (
                    session.query(OHLC)
                    .filter(
                        and_(
                            OHLC.symbol == symbol,
                            OHLC.timeframe == timeframe
                        )
                    )
                    .order_by(desc(OHLC.timestamp))
                    .limit(limit)
                    .all()
                )
                return OHLCRepository._ohlc_to_dict_list(ohlc_bars)
            else:
                with get_db_session() as db:
                    ohlc_bars = (
                        db.query(OHLC)
                        .filter(
                            and_(
                                OHLC.symbol == symbol,
                                OHLC.timeframe == timeframe
                            )
                        )
                        .order_by(desc(OHLC.timestamp))
                        .limit(limit)
                        .all()
                    )
                    return OHLCRepository._ohlc_to_dict_list(ohlc_bars)

        except Exception as e:
            logger.error(f"Error fetching recent OHLC: {e}")
            return []

    @staticmethod
    def get_ohlc_by_timerange(
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        session: Optional[Session] = None
    ) -> List[Dict]:
        """
        Get OHLC data within a time range

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (1s, 1m, 5m)
            start_time: Start of time range
            end_time: End of time range
            session: Optional database session

        Returns:
            List of OHLC data dictionaries
        """
        try:
            if session:
                ohlc_bars = (
                    session.query(OHLC)
                    .filter(
                        and_(
                            OHLC.symbol == symbol,
                            OHLC.timeframe == timeframe,
                            OHLC.timestamp >= start_time,
                            OHLC.timestamp <= end_time
                        )
                    )
                    .order_by(OHLC.timestamp)
                    .all()
                )
                return OHLCRepository._ohlc_to_dict_list(ohlc_bars)
            else:
                with get_db_session() as db:
                    ohlc_bars = (
                        db.query(OHLC)
                        .filter(
                            and_(
                                OHLC.symbol == symbol,
                                OHLC.timeframe == timeframe,
                                OHLC.timestamp >= start_time,
                                OHLC.timestamp <= end_time
                            )
                        )
                        .order_by(OHLC.timestamp)
                        .all()
                    )
                    return OHLCRepository._ohlc_to_dict_list(ohlc_bars)
        except Exception as e:
            logger.error(f"Error fetching OHLC by timerange: {e}")
            return []

    @staticmethod
    def _ohlc_to_dict_list(ohlc_bars: List[OHLC]) -> List[Dict]:
        """Convert OHLC objects to dictionaries"""
        return [
            {
                'timestamp': bar.timestamp,
                'symbol': bar.symbol,
                'timeframe': bar.timeframe,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'trade_count': bar.trade_count,
                'vwap': bar.vwap
            }
            for bar in ohlc_bars
        ]

    @staticmethod
    def get_ohlc_count(
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        session: Optional[Session] = None
    ) -> int:
        """
        Get total count of OHLC records

        Args:
            symbol: Optional symbol to filter by
            timeframe: Optional timeframe to filter by
            session: Optional database session

        Returns:
            Number of records
        """
        try:
            if session:
                query = session.query(OHLC)
                if symbol:
                    query = query.filter(OHLC.symbol == symbol)
                if timeframe:
                    query = query.filter(OHLC.timeframe == timeframe)
                return query.count()
            else:
                with get_db_session() as db:
                    query = db.query(OHLC)
                    if symbol:
                        query = query.filter(OHLC.symbol == symbol)
                    if timeframe:
                        query = query.filter(OHLC.timeframe == timeframe)
                    return query.count()
        except Exception as e:
            logger.error(f"Error counting OHLC records: {e}")
            return 0

    @staticmethod
    def delete_old_ohlc(days_to_keep: int = 30, session: Optional[Session] = None) -> int:
        """
        Delete OHLC data older than specified days

        Args:
            days_to_keep: Number of days to retain
            session: Optional database session

        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        try:
            if session:
                deleted = (
                    session.query(OHLC)
                    .filter(OHLC.timestamp < cutoff_date)
                    .delete()
                )
                session.commit()
                logger.info(f"Deleted {deleted} old OHLC records (older than {cutoff_date})")
                return deleted
            else:
                with get_db_session() as db:
                    deleted = (
                        db.query(OHLC)
                        .filter(OHLC.timestamp < cutoff_date)
                        .delete()
                    )
                    db.commit()
                    logger.info(f"Deleted {deleted} old OHLC records (older than {cutoff_date})")
                    return deleted
        except Exception as e:
            logger.error(f"Error deleting old OHLC records: {e}")
            return 0

    @staticmethod
    def get_available_timeframes(symbol: str, session: Optional[Session] = None) -> List[str]:
        """
        Get list of timeframes available for a symbol

        Args:
            symbol: Trading pair symbol
            session: Optional database session

        Returns:
            List of unique timeframes
        """
        try:
            if session:
                result = (
                    session.query(OHLC.timeframe)
                    .filter(OHLC.symbol == symbol)
                    .distinct()
                    .all()
                )
                return [r[0] for r in result]
            else:
                with get_db_session() as db:
                    result = (
                        db.query(OHLC.timeframe)
                        .filter(OHLC.symbol == symbol)
                        .distinct()
                        .all()
                    )
                    return [r[0] for r in result]
        except Exception as e:
            logger.error(f"Error fetching available timeframes: {e}")
            return []
