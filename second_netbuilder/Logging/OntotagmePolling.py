#########################################################################################################################
# This class has been developed to query Ontotagme about the process progress.                                          #
# The atexit module has been employed for setting the "threading.Event" and waits on the "threading.Thread" instance    #
# of the background task via the atexit.register() function. This allows the process to destroy a thread when it will   #
# be unlisted.                                                                                                          #
# We can define a function named stop_background() that takes the "threading.Event" and "threading.Thread" instances as #
# arguments then sets the event and waits on the thread.                                                                #
#########################################################################################################################
# IMPORTING
import asyncio
from   time             import sleep
from   threading        import Thread
from   threading        import Event
from   Utility.Utility  import Utility as Ut
import atexit
import requests
import json
import redis


STOP_MESS = "Unable to compute OntoTagME progress"


class OntoPolling:
    def __init__(self, token_id):
        self.thread  = None
        self.utility = Ut()
        self.create_thread(token_id)

    # BACKGROUND TASK
    def task(self, event, token_id):
        last_message = ""
        red = redis.from_url(self.utility.BROKER_URI)
        # FOREVER RUNNING UNTIL STOPPED EVENT IS TRIGGERED
        get_uri = self.utility.URL_FOR_LOG.format(token=token_id)
        while not event.is_set():
            # REQUEST EACH 1 SECOND TO ONTOTAGME ABOUT LOGGING
            sleep(1)
            log_data = requests.get(get_uri)
            if log_data.status_code != 200:
                print("THERE WAS AN ERROR DUE TO ONTOTAGME PROBLEM")
                print("ERROR:", log_data.content)
                break
            response = json.loads(log_data.content)
            if response["progress"] == STOP_MESS: break
            if response["progress"] == last_message: continue
            self.utility.task_status_updating_onto(response["progress"], 0.0, token_id, red)
            last_message = response["progress"]
        print('Background done')

    # STOP BACKGROUND TASK GRACEFULLY BEFORE EXIT
    @staticmethod
    def stop_background(stop_event_, thread):
        print('At exit stopping')
        # BACKGROUND THREAD STOP
        stop_event_.set()
        # WAIT FOR THE BACKGROUND THREAD TO STOP
        thread.join()
        print('At exit done')

    def create_thread(self, req_id):
        # CREATE STOP EVENT
        stop_event  = Event()
        # CREATE AND START BACKGROUND THREAD
        self.thread = Thread(target=self.task, args=(stop_event, req_id,), daemon=True, name="Onto logging Background")
        self.thread.start()
        atexit.register(self.stop_background, stop_event, self.thread)
