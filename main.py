import logging
from config import logger, STUDENT_PROFILE, SIMILARITY_THRESHOLD
from scraper import EventScraper
from embedding_matcher import EmbeddingMatcher
from calendar_manager import CalendarManager
from typing import List, Dict, Any

# Ensure all loggers are set up before execution
logger.info("Initializing HackBounty AI Agent...")

def run_agent():
    """
    Main function to execute the HackBounty AI agent workflow.
    """
    # 1. Initialization
    scraper = EventScraper(base_url="https://devpost.com/hackathons") # Replace with a real event site
    matcher = EmbeddingMatcher()
    calendar_manager = CalendarManager()

    if not calendar_manager.service:
        logger.error("Agent terminated: Google Calendar service failed to initialize (check 'credentials.json').")
        return

    # 2. Data Acquisition
    potential_events = scraper.get_events()
    if not potential_events:
        logger.info("No events found to process. Exiting.")
        return

    # 3. Filtering and Matching (EDA/SBERT)
    logger.info(f"Matching {len(potential_events)} events against student profile...")
    
    # The matcher handles SBERT embedding and the initial eligibility/deadline filtering
    relevant_events = matcher.find_best_matches(
        student_profile=STUDENT_PROFILE,
        events=potential_events,
        threshold=SIMILARITY_THRESHOLD
    )

    if not relevant_events:
        logger.info("No events met the relevance threshold. Exiting.")
        return

    # 4. Scheduling and Alerting (Google Calendar API)
    logger.info(f"Found {len(relevant_events)} highly relevant events. Scheduling them now.")

    events_scheduled_count = 0
    for event in relevant_events:
        if calendar_manager.create_event(event):
            events_scheduled_count += 1
        
    # 5. Final Report
    print("\n" + "="*50)
    print("         HackBounty Agent Run Complete")
    print("="*50)
    print(f"Total Potential Events Scraped: {len(potential_events)}")
    print(f"Relevance Threshold Used: {SIMILARITY_THRESHOLD}")
    print(f"Highly Relevant/Eligible Events Found: {len(relevant_events)}")
    print(f"Events Successfully Scheduled in Google Calendar: {events_scheduled_count}")
    print(f"Check 'hackbounty.log' for detailed output.")
    print("="*50 + "\n")


if __name__ == "__main__":
    try:
        run_agent()
    except KeyboardInterrupt:
        logger.warning("Agent execution interrupted by user.")
    except Exception as e:
        logger.critical(f"An unexpected fatal error occurred: {e}", exc_info=True)
