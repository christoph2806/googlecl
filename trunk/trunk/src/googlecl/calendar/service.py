"""
Service details and instances for the Picasa service.

Some use cases:
Add event:
  calendar add "Lunch with Tony on Tuesday at 12:00" 

List events for today:
  calendar today
  
Created on May 24, 2010

@author: Tom Miller

"""
__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import datetime
import gdata.calendar.service
import util
from googlecl.calendar import SECTION_HEADER


class CalendarServiceCL(gdata.calendar.service.CalendarService,
                        util.BaseServiceCL):

  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as event titles. (Default False)
      tags_prompt: Indicates if while inserting events, instance should prompt
                   for tags for each photo. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting a calendar or event. (Default True)
              
    """
    gdata.calendar.service.CalendarService.__init__(self)
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)

  def quick_add_event(self, quick_add_string):
    """Add an event using the Calendar Quick Add feature.
    
    Keyword arguments:
      quick_add_string: String to be parsed by the Calendar service, as if it
                        was entered via the "Quick Add" function.

    Returns:
      The event that was added.
    
    """
    import atom
    event = gdata.calendar.CalendarEventEntry()
    event.content = atom.Content(text=quick_add_string)
    event.quick_add = gdata.calendar.QuickAdd(value='true') 
    return self.InsertEvent(event, '/calendar/feeds/default/private/full')

  QuickAddEvent = quick_add_event

  def get_events(self, date=None, title=None, query=None):
    """Get events.
    
    Keyword arguments:
      date: Date of the event(s). Sets one or both of start-min or start-max in
            the uri. Must follow the format 'YYYY-MM-DD' in one of three ways:
              '<format>' - set a start date.
              '<format>,<format>' - set a start and end date.
              ',<format>' - set an end date.
            Default None for any date.
      title: Title to look for in the event, supporting regular expressions.
             Default None for any title.
      query: Query string (not encoded) for doing full-text searches on event
             titles and content.
                 
    Returns:
      List of events from all calendars that match the given params.
                  
    """
    query = gdata.calendar.service.CalendarEventQuery(text_query=query)
    if date:
      start, junk, end = date.partition(',')
      if start:
        query.start_min = start
      if end:
        query.start_max = end
    return self.GetEntries(query.ToUri(), title,
                           converter=gdata.calendar.CalendarEventFeedFromString)

  GetEvents = get_events

  def is_token_valid(self):
    """Check that the token being used is valid."""
    return util.BaseServiceCL.IsTokenValid(self,
                                    '/calendar/feeds/default/allcalendars/full')

  IsTokenValid = is_token_valid


service_class = CalendarServiceCL


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#  
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_list(client, options, args):
  entries = client.get_events(date=options.date,
                              title=options.title,
                              query=options.query)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.get_config_option(SECTION_HEADER, 'list_style').split(',')
  for e in entries:
    print util.entry_to_string(e, style_list, delimiter=options.delimiter)


def _run_list_today(client, options, args):
  now = datetime.datetime.now()
  tomorrow = now + datetime.timedelta(days=1)
  options.date = now.strftime(util.DATE_FORMAT) + ',' + \
                 tomorrow.strftime(util.DATE_FORMAT)
  _run_list(client, options, args)


def _run_add(client, options, args):
  client.quick_add_event(args[0])


def _run_delete(client, options, args):
  events = client.get_events(options.date, options.title, options.query)
  client.Delete(events, 'event',
                util.config.get('GENERAL', 'delete_by_default'))


tasks = {'list': util.Task('List events on primary calendar',
                           callback=_run_list,
                           required=['delimiter'],
                           optional=['title', 'query', 'date']),
         'today': util.Task('List events for today',
                            callback=_run_list_today,
                            required='delimiter', optional=['title', 'query']),
         'add': util.Task('Add event to primary calendar', callback=_run_add,
                          args_desc='QUICK_ADD_TEXT'),
         'delete': util.Task('Delete event from primary calendar',
                             callback=_run_delete,
                             required=[['title', 'query']], optional='date')}