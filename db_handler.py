from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

Base = declarative_base()

class SystemSnapshot(Base):
    __tablename__ = 'system_snapshots'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    diagnostics_data = Column(JSON)
    analysis_data = Column(JSON)
    changes_data = Column(JSON)

class DatabaseHandler:
    def __init__(self, db_url: str):
        """Initialize the database handler with the given database URL."""
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save_snapshot(self, diagnostics_data: dict, analysis_data: dict, changes_data: dict) -> int:
        """Save a complete system snapshot to the database.

        Args:
            diagnostics_data (dict): The diagnostics data to save.
            analysis_data (dict): The analysis data to save.
            changes_data (dict): The changes data to save.

        Returns:
            int: The ID of the saved snapshot.
        """
        session = self.Session()
        try:
            snapshot = SystemSnapshot(
                diagnostics_data=diagnostics_data,
                analysis_data=analysis_data,
                changes_data=changes_data
            )
            session.add(snapshot)
            session.commit()
            logger.info(f"Snapshot saved with ID: {snapshot.id}")
            return snapshot.id
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            session.rollback()  # Rollback in case of error
            raise
        finally:
            session.close()
    
    def get_latest_snapshot(self) -> SystemSnapshot:
        """Get the most recent system snapshot.

        Returns:
            SystemSnapshot: The latest snapshot or None if no snapshots exist.
        """
        session = self.Session()
        try:
            latest_snapshot = session.query(SystemSnapshot).order_by(
                SystemSnapshot.timestamp.desc()
            ).first()
            logger.info(f"Retrieved latest snapshot: {latest_snapshot.id if latest_snapshot else 'None'}")
            return latest_snapshot
        except Exception as e:
            logger.error(f"Error retrieving latest snapshot: {e}")
            raise
        finally:
            session.close()
    
    def get_snapshots_range(self, start_date: datetime, end_date: datetime) -> list:
        """Get system snapshots within a date range.

        Args:
            start_date (datetime): The start date of the range.
            end_date (datetime): The end date of the range.

        Returns:
            list: A list of SystemSnapshot objects within the specified date range.
        """
        session = self.Session()
        try:
            snapshots = session.query(SystemSnapshot).filter(
                SystemSnapshot.timestamp.between(start_date, end_date)
            ).all()
            logger.info(f"Retrieved {len(snapshots)} snapshots between {start_date} and {end_date}.")
            return snapshots
        except Exception as e:
            logger.error(f"Error retrieving snapshots in range: {e}")
            raise
        finally:
            session.close()