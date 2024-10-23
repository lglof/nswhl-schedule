from typing_extensions import override
from openai import AssistantEventHandler, OpenAI
 
client = OpenAI()

assistant = client.beta.assistants.create(
    instructions="""You are a hockey league scheduling assistant. 
    You will be provided with teams divided into divisions, some teams will have restrictions on their games.
    You'll also be provided a text file that outlines the available games. Some of the games in that file already
    have teams assigned to them, you'll have to take those into account when assiging teams to games.
    It's your job to assign teams to the provided games. Teams can only play against other teams within their division,
    and can't play more than one game on the same day. You will respond in csv format with the following
    column titles: Division, Away Team, Home Team, Date, Start Time, Venue. The date, start time, and
    venue of each row should match the values in the corresponding row in the initially provided file.
    Do not confirm any information, just go right to providing the csv formatted output.
    Each team is to have a 24 game season. 12 home games 
    and 12 away games. There are 38 teams across all divisions. The attached files 
    contain the information about each team and the complete list of the games we 
    have available. There are 366 games without teams assigned to them on that list, 
    please take into account the games that already have teams assigned to them when 
    assigning teams. This is 7 less than needed to create a full season schedule. 
    Provide extra lines at the end of the output to show the missing matchups but don't 
    give times, dates, or venues for those games""",
    name="Scheduler v2",
    tools=[{"type": "file_search"}],
    model="gpt-4o-mini",
)
print(assistant)

# asst_DXvWALfyh0uDGmKOK6qHlOYx

# Upload the user provided file to OpenAI
schedule_message_file = client.files.create(
  file=open("lars-nswhl-master-schedule.xlsx - Master Schedule.pdf", "rb"), purpose="assistants"
)

teams_message_file = client.files.create(
    file=open("teams.txt", "rb"), purpose="assistants"
)
 
# Create a thread and attach the file to the message
thread = client.beta.threads.create(
  messages=[
    {
        "role": "user",
        "content": """Here are the files containing information on the teams and the games to be assigned.
        Do not confirm details, just provide the csv formatted output containing all the games in the season and their assigned teams""",
        "attachments": [
            { "file_id": teams_message_file.id, "tools": [{"type": "file_search"}] },
            { "file_id": schedule_message_file.id, "tools": [{"type": "file_search"}] },
        ],
    },
  ]
)
 
# The thread now has a vector store with that file in its tool resources.
print(thread.tool_resources.file_search)
print(schedule_message_file.id)

output_file = open("test2.csv", "w");

class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    @override
    def on_message_done(self, message) -> None:
        # print a citation to the file searched
        message_content = message.content[0].text

        output_file.write(message_content.value)


# Then, we use the stream SDK helper
# with the EventHandler class to create the Run
# and stream the response.

with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Given the information about each team and the list of available games, please create a schedule for the season",
    event_handler=EventHandler(),
) as stream:
    stream.until_done()
output_file.close()