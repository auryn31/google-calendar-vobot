import lvgl as lv
import peripherals
import urequests
import json
import time
from machine import Timer

# App Name
NAME = "Calendar Events"

# Configuration
API_URL = "api url"
HARDCODED_TOKEN = "..."
CHECK_INTERVAL = 60000  # Check events every minute
ALERT_BEFORE_MEETING = 60  # Seconds to alert before meeting

# LVGL widgets
scr = None
label = None
next_meeting_label = None

# State variables
current_events = []
meeting_rows = []  # For the row objects
meeting_labels = []  # Add this new list for labels
alert_timer = None
last_api_call = 0

def format_time(iso_time):
    # Convert ISO time string to readable format
    try:
        # Basic time parsing since micropython doesn't have datetime
        time_str = iso_time.split('T')[1][:5]  # Get HH:MM
        return time_str
    except:
        return "??:??"

def get_current_time():
    return time.time()

def fetch_events():
    bearer = "Bearer {}"
    try:
        headers = {
            'Authorization': bearer.format(HARDCODED_TOKEN),
            'Content-Type': 'application/json'
        }
        print("Fetching events from:", API_URL)  # Debug print
        response = urequests.get(API_URL, headers=headers)
        print("Response status:", response.status_code)  # Debug print
        if response.status_code == 200:
            events = json.loads(response.text)
            print("Fetched events:", events)  # Debug print
            return events
        print("Error response:", response.text)  # Debug print
        return []
    except Exception as e:
        print("Error fetching events:", e)
        return []

def check_upcoming_meeting():
    global current_events
    current_time = get_current_time()
    has_meeting = False
    
    print(f"\nCurrent time: {current_time}")
    
    for event in current_events:
        try:
            # Parse the event time
            start_datetime = event['start']['dateTime']
            end_datetime = event['end']['dateTime']
            
            # Parse start time
            date_str = start_datetime.split('T')[0]  # Get YYYY-MM-DD
            time_str = start_datetime.split('T')[1].split('+')[0]  # Get HH:MM:SS
            tz_offset = int(start_datetime.split('+')[1].split(':')[0])  # Get timezone offset
            
            # Parse date and time components
            year, month, day = [int(x) for x in date_str.split('-')]
            hours, minutes, seconds = [int(x) for x in time_str.split(':')]
            
            # Adjust for timezone
            hours -= tz_offset  # Subtract timezone offset to get UTC
            
            # Create timestamp
            start_time = time.mktime((year, month, day, hours, minutes, 0, 0, 0, 0))
            
            # Parse end time similarly
            end_date_str = end_datetime.split('T')[0]
            end_time_str = end_datetime.split('T')[1].split('+')[0]
            end_tz_offset = int(end_datetime.split('+')[1].split(':')[0])
            
            end_year, end_month, end_day = [int(x) for x in end_date_str.split('-')]
            end_hours, end_minutes, end_seconds = [int(x) for x in end_time_str.split(':')]
            
            # Adjust for timezone
            end_hours -= end_tz_offset
            
            end_time = time.mktime((end_year, end_month, end_day, end_hours, end_minutes, 0, 0, 0, 0))
            
            # Debug prints
            print(f"Event: {event.get('summary', 'Untitled')}")
            print(f"Start: {start_datetime} -> {start_time}")
            print(f"End: {end_datetime} -> {end_time}")
            print(f"Current: {current_time}")
            print(f"Time until start: {start_time - current_time} seconds")
            
            
            # Check meeting status
            if current_time >= start_time and current_time <= end_time:
                print("Meeting in progress - RED")
                peripherals.ambient_light.set_color([(255, 0, 0)], True)
                peripherals.ambient_light.brightness(100)
                has_meeting = True
                break
            elif 0 < (start_time - current_time) <= 300:  # Within 5 minutes
                print("Meeting starting soon - YELLOW")
                peripherals.ambient_light.set_color([(255, 255, 0)], True)
                peripherals.ambient_light.brightness(100)
                has_meeting = True
                break
            
        except Exception as e:
            print(f"Error checking meeting time: {e}")
            print(f"Event data: {event}")
            continue
    
    # No immediate meetings, set to yellow
    if not has_meeting:
        print("No immediate meetings - GREEN")
        peripherals.ambient_light.acquire()
        peripherals.ambient_light.set_color([(0, 255, 0)], True)
        peripherals.ambient_light.brightness(100)
    

def format_relative_time(iso_time):
    try:
        # Parse the ISO datetime string
        date_str = iso_time.split('T')[0]  # Get YYYY-MM-DD
        time_str = iso_time.split('T')[1].split('+')[0]  # Get HH:MM:SS
        tz_offset = int(iso_time.split('+')[1].split(':')[0])  # Get timezone offset

        
        # Get components
        year, month, day = map(int, date_str.split('-'))
        hours, minutes, _ = time_str.split(':')
        
        hours = int(hours) - tz_offset
        # Create a time tuple
        event_time = time.mktime((year, month, day, int(hours), int(minutes), 0, 0, 0, 0))
        
        # Calculate difference in minutes
        diff_minutes = max(0, int((event_time - get_current_time()) / 60))
        hours = diff_minutes // 60
        minutes = diff_minutes % 60
        print(hours)
        print(minutes)
        if hours > 0:
            return f"in {hours}h {minutes}m"
        if minutes > 0:
            return f"in {minutes}m"
        else:
            return "ongoing"
    except Exception as e:
        print(f"Error formatting time: {e}")  # Debug print
        return "??"

def get_future_events(events, limit=3):
    current_time = get_current_time()
    future_events = []
    
    for event in events:
        try:
            # Parse the ISO datetime string
            date_str = event['end']['dateTime'].split('T')[0]  # Get YYYY-MM-DD
            time_str = event['end']['dateTime'].split('T')[1].split('+')[0]  # Get HH:MM:SS
            
            # Get just the hours and minutes
            hours, minutes, _ = time_str.split(':')
            
            # Create a time tuple (year, month, day, hour, minute, second, weekday, yearday)
            year, month, day = map(int, date_str.split('-'))
            event_time = time.mktime((year, month, day, int(hours), int(minutes), 0, 0, 0, 0))
            
            if event_time > current_time:
                future_events.append(event)
                if len(future_events) >= limit:
                    break
        except Exception as e:
            print(f"Error parsing event time: {e}")  # Debug print
            continue
    
    return future_events

def display_events(events):
    """Create and display the UI for the given events"""
    # Create main screen
    scr = lv.obj()
    
    # Container for meeting rows
    container = lv.obj(scr)
    container.set_size(320, 240)
    container.center()
    container.set_style_bg_color(lv.color_make(0, 0, 0), 0)
    container.set_style_pad_all(10, 0)
    
    # Get up to 3 future events
    future_events = get_future_events(events, limit=3)
    
    if not future_events:
        # Create single row for "no meetings" message
        row = lv.obj(container)
        row.set_size(300, 60)
        row.align(lv.ALIGN.TOP_LEFT, 0, 0)
        row.set_style_bg_color(lv.color_make(40, 40, 40), 0)
        row.set_style_radius(10, 0)
        row.set_style_pad_all(5, 0)
        
        label = lv.label(row)
        label.align(lv.ALIGN.LEFT_MID, 10, 0)
        label.set_long_mode(lv.label.LONG.WRAP)
        label.set_width(260)
        label.set_text("No more meetings today")
    else:
        # Create row for each event
        for i, event in enumerate(future_events):
            row = lv.obj(container)
            row.set_size(296, 60)
            row.align(lv.ALIGN.TOP_LEFT, 0, i * 70)
            row.set_style_bg_color(lv.color_make(40, 40, 40), 0)
            row.set_style_radius(10, 0)
            row.set_style_pad_all(5, 0)
            
            label = lv.label(row)
            label.align(lv.ALIGN.LEFT_MID, 10, 0)
            label.set_long_mode(lv.label.LONG.WRAP)
            label.set_width(270)
            
            relative_time = format_relative_time(event['start']['dateTime'])
            summary = event['summary'] if 'summary' in event else 'Untitled'
            label.set_text(f"{summary}\n{relative_time}")
    
    # Load the screen
    lv.scr_load(scr)
    return scr

async def on_start():
    global current_events, last_api_call
    print('on start')
    
    # Initial fetch and display
    peripherals.ambient_light.acquire()
    current_events = fetch_events()
    last_api_call = get_current_time()
    display_events(current_events)

async def on_running_foreground():
    global current_events, last_api_call
    current_time = get_current_time()
    
    print("on_running_foreground")
    print(current_time - last_api_call)
    print(current_time)
    print(last_api_call)
    try:
        # Only fetch events if a minute has passed
        if current_time - last_api_call >= 60 or current_time - last_api_call < 0:
            print("Fetching new events...")
            current_events = fetch_events()
            last_api_call = current_time
            display_events(current_events)
        
        # Check for upcoming meetings
        check_upcoming_meeting()
    except Exception as e:
        print("Error in foreground task:", e)
        raise

async def on_stop():
    global scr
    print('on stop')
    

    peripherals.ambient_light.set_color([(0, 0, 0)], True)
    peripherals.ambient_light.release()

