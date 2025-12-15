"""
Repository for tick data database operations
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from loguru import logger

from backend.storage.models import TickData
from backend.storage.database import get_db_session


class TickDataRepository:
    """
    Data access layer for tick data operations
    
    Handles:
    - Batch inserts
    - Queries by symbol and time range
    - Data cleanup and retention
    """
    
    @staticmethod
    def insert_batch(records: List[Dict], session: Optional[Session] = None) -> int:
        """
        Insert multiple tick records in a single transaction
        
        Args:
            records: List of tick data dictionaries
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
                    return TickDataRepository._do_insert(records, db)
            else:
                return TickDataRepository._do_insert(records, session)
                
        except Exception as e:
            logger.error(f"Error inserting tick data batch: {e}")
            raise
    
    @staticmethod
    def _do_insert(records: List[Dict], db: Session) -> int:
        """
        Internal method to perform batch insert
        
        Args:
            records: List of dictionaries with tick data
            db: Database session
            
        Returns:
            Number of records inserted
        """
        tick_objects = []
        
        for record in records:
            tick = TickData(
                timestamp=record["timestamp"],
                symbol=record["symbol"],
                price=record["price"],
                quantity=record["quantity"],
                volume=record.get("volume", record["price"] * record["quantity"])
            )
            tick_objects.append(tick)
        
        # Add all objects and let SQLAlchemy handle IDs
        db.add_all(tick_objects)
        db.commit()
        
        logger.debug(f"Inserted {len(tick_objects)} tick records")
        return len(tick_objects)

    @staticmethod
    def get_recent_ticks(
        symbol: str,
        limit: int = 100,
        session: Optional[Session] = None
    ) -> List[Dict]:  # Changed return type to List[Dict]
        """
        Get most recent tick data for a symbol

        Args:
            symbol: Trading pair symbol
            limit: Maximum number of records to return
            session: Optional database session

        Returns:
            List of tick data dictionaries (detached from session)
        """
        try:
            if session:
                ticks = (
                    session.query(TickData)
                    .filter(TickData.symbol == symbol)
                    .order_by(desc(TickData.timestamp))
                    .limit(limit)
                    .all()
                )
                # Convert to dictionaries while session is active
                return [
                    {
                        'timestamp': tick.timestamp,
                        'symbol': tick.symbol,
                        'price': tick.price,
                        'quantity': tick.quantity,
                        'volume': tick.volume
                    }
                    for tick in ticks
                ]
            else:
                with get_db_session() as db:
                    ticks = (
                        db.query(TickData)
                        .filter(TickData.symbol == symbol)
                        .order_by(desc(TickData.timestamp))
                        .limit(limit)
                        .all()
                    )
                    # Convert to dictionaries while session is active
                    return [
                        {
                            'timestamp': tick.timestamp,
                            'symbol': tick.symbol,
                            'price': tick.price,
                            'quantity': tick.quantity,
                            'volume': tick.volume
                        }
                        for tick in ticks
                    ]

        except Exception as e:
            logger.error(f"Error fetching recent ticks: {e}")
            return []
    
    @staticmethod
    def get_ticks_by_timerange(
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        session: Optional[Session] = None
    ) -> List[Dict]:
        """
        Get tick data within a time range

        Args:
            symbol: Trading pair symbol
            start_time: Start of time range
            end_time: End of time range
            session: Optional database session

        Returns:
            List of tick data dictionaries (detached from session)
        """
        try:
            if session:
                ticks = (
                    session.query(TickData)
                    .filter(
                        and_(
                            TickData.symbol == symbol,
                            TickData.timestamp >= start_time,
                            TickData.timestamp <= end_time
                        )
                    )
                    .order_by(TickData.timestamp)
                    .all()
                )
                # Convert to dictionaries while session is active
                return [
                    {
                        'timestamp': tick.timestamp,
                        'symbol': tick.symbol,
                        'price': tick.price,
                        'quantity': tick.quantity,
                        'volume': tick.volume
                    }
                    for tick in ticks
                ]
            else:
                with get_db_session() as db:
                    ticks = (
                        db.query(TickData)
                        .filter(
                            and_(
                                TickData.symbol == symbol,
                                TickData.timestamp >= start_time,
                                TickData.timestamp <= end_time
                            )
                        )
                        .order_by(TickData.timestamp)
                        .all()
                    )
                    # Convert to dictionaries while session is active
                    return [
                        {
                            'timestamp': tick.timestamp,
                            'symbol': tick.symbol,
                            'price': tick.price,
                            'quantity': tick.quantity,
                            'volume': tick.volume
                        }
                        for tick in ticks
                    ]
        except Exception as e:
            logger.error(f"Error fetching ticks by timerange: {e}")
            return []
    
    @staticmethod
    def get_tick_count(symbol: Optional[str] = None, session: Optional[Session] = None) -> int:
        """
        Get total count of tick records
        
        Args:
            symbol: Optional symbol to filter by
            session: Optional database session
            
        Returns:
            Number of records
        """
        try:
            if session:
                query = session.query(TickData)
                if symbol:
                    query = query.filter(TickData.symbol == symbol)
                return query.count()
            else:
                with get_db_session() as db:
                    query = db.query(TickData)
                    if symbol:
                        query = query.filter(TickData.symbol == symbol)
                    return query.count()
        except Exception as e:
            logger.error(f"Error counting ticks: {e}")
            return 0
    
    @staticmethod
    def delete_old_ticks(days_to_keep: int = 7, session: Optional[Session] = None) -> int:
        """
        Delete tick data older than specified days (for data retention)
        
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
                    session.query(TickData)
                    .filter(TickData.timestamp < cutoff_date)
                    .delete()
                )
                session.commit()
                logger.info(f"Deleted {deleted} old tick records (older than {cutoff_date})")
                return deleted
            else:
                with get_db_session() as db:
                    deleted = (
                        db.query(TickData)
                        .filter(TickData.timestamp < cutoff_date)
                        .delete()
                    )
                    db.commit()
                    logger.info(f"Deleted {deleted} old tick records (older than {cutoff_date})")
                    return deleted
        except Exception as e:
            logger.error(f"Error deleting old ticks: {e}")
            return 0
    
    @staticmethod
    def get_available_symbols(session: Optional[Session] = None) -> List[str]:
        """
        Get list of symbols that have tick data
        
        Args:
            session: Optional database session
            
        Returns:
            List of unique symbols
        """
        try:
            if session:
                result = session.query(TickData.symbol).distinct().all()
                return [r[0] for r in result]
            else:
                with get_db_session() as db:
                    result = db.query(TickData.symbol).distinct().all()
                    return [r[0] for r in result]
        except Exception as e:
            logger.error(f"Error fetching available symbols: {e}")
            return []
