from dotenv import load_dotenv
import discord
import os
from openai import OpenAI
import sqlite3
import json

# Load environment variables from .env file
load_dotenv()

# connect to sqlite db
dbconn = sqlite3.connect('sampledb/db.sqlite')
dbcursor = dbconn.cursor()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True # Ensure that your bot can read message content
d_client = discord.Client(intents=intents)

tools = [
        {
            "type": "function",
            "name": "query",
            "description": "Run a SQL query on the database",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "An SQL query to execute on the sqlite database",
                    },
                },
                "required": ["sql"],
            },
        },
    ]

def query(sql):
    print (f"Executing SQL: {sql}")
    try:
        dbcursor.execute(sql)

        # Get column names from the cursor description
        # This is crucial for creating dictionaries
        column_names = [description[0] for description in dbcursor.description]

        rows = dbcursor.fetchall()

        # Convert list of tuples to list of dictionaries
        results_as_dicts = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            results_as_dicts.append(row_dict)

        # return the results in JSON format
        return json.dumps(results_as_dicts, indent=4)
    except sqlite3.Error as e:
        err = f"Database error: {e}"
        print (err)
        return err
    except Exception as e:
        err = f"An unexpected error occurred: {e}"
        print (err)
        return err

ai_client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
def answer_question(question):
    input_list = [
            {"role": "user", "content": question},
        ]

    while True:
        response = ai_client.responses.create(
                model="gpt-5",
                reasoning={"effort": "low"},
                instructions="""
                You are a discord bot that assists the company Sakila which is a DVD rental company.
                
                Explanation of the sqlite db
                ## Core Film and Actor Information

                This group describes the movies themselves and the people in them.

                - **`FILM`**: This is a central table listing all films. It includes details like `TITLE`, `DESCRIPTION`, `RELEASE_YEAR`, `RATING`, and `LENGTH`.
                    
                - **`ACTOR`**: This table lists all actors with their `FIRST_NAME` and `LAST_NAME`.
                    
                - **`FILM_ACTOR`**: This is a **junction table** that creates a **many-to-many relationship** between `FILM` and `ACTOR`. This means one film can have many actors, and one actor can be in many films.
                    
                - **`CATEGORY`**: This table lists film genres, like 'Action', 'Comedy', or 'Horror'.
                    
                - **`FILM_CATEGORY`**: This junction table creates a **many-to-many relationship** between `FILM` and `CATEGORY`. A film can belong to multiple categories, and a category can contain many films.
                    
                - **`LANGUAGE`**: This table lists languages (e.g., 'English', 'Japanese'). The `FILM` table links to this twice: once for the film's main `LANGUAGE_ID` and once for its `ORIGINAL_LANGUAGE_ID`.
                    

                ---

                ## Store Inventory and Staff

                This group describes the physical stores and what they have in stock.

                - **`STORE`**: Represents a physical store location. It has a foreign key for its `ADDRESS_ID` and a key to link to its manager (`MANAGER_STAFF_ID`).
                    
                - **`INVENTORY`**: This table tracks the individual copies (e.g., specific DVDs or Blu-rays) of films. It links `FILM_ID` (which film is it?) to `STORE_ID` (which store has it?). This means one film (like "Titanic") can have many inventory items, and one store can have many inventory items.
                    
                - **`STAFF`**: This table lists all employees. Each staff member is linked to one `STORE_ID` (where they work) and one `ADDRESS_ID` (where they live). The `STORE` table also links back to this table to identify its manager.
                    

                ---

                ## Customer, Rental, and Payment Logic

                This is the core business transaction group, tracking who rents what.

                - **`CUSTOMER`**: This table stores customer information, including name, email, and their "home" `STORE_ID`. It also links to an `ADDRESS_ID`.
                    
                - **`RENTAL`**: This table records every time a customer rents a movie. It links together:
                    
                    - `INVENTORY_ID`: Which specific DVD was rented.
                        
                    - `CUSTOMER_ID`: Who rented it.
                        
                    - `STAFF_ID`: Which employee processed the rental.
                        
                    - It also stores the `RENTAL_DATE` and `RETURN_DATE`.
                        
                - **`PAYMENT`**: This table records all customer payments. Each payment is linked to the `CUSTOMER_ID` who paid, the `STAFF_ID` who processed the payment, and the specific `RENTAL_ID` the payment was for. This one-to-many relationship from `RENTAL` to `PAYMENT` allows for multiple payments for a single rental (e.g., an initial fee and a later late fee).
                    

                ---

                ## Location and Address Data

                This group is a normalized structure for handling all physical addresses in the database.

                - **`COUNTRY`**: A list of countries (e.g., 'USA', 'Canada').
                    
                - **`CITY`**: A list of cities. Each city is linked to its `COUNTRY_ID`.
                    
                - **`ADDRESS`**: A list of specific street addresses. Each address is linked to its `CITY_ID` and includes details like `ADDRESS`, `DISTRICT`, and `POSTAL_CODE`.
                    
                - This `ADDRESS` table is then used by the **`CUSTOMER`**, **`STAFF`**, and **`STORE`** tables, giving each of them a physical location.

                You will be given a question about the Sakila business. Please use the DB information and tools available to you to answer the question for the user.
                """,
                tools=tools,
                input=input_list
            )
        
        input_list += response.output

        called_function = False
        for item in response.output:
            if item.type == "function_call":
                called_function = True
                
                if item.name == "query":
                    func_in = json.loads(item.arguments)
                    print(func_in)
                    func_resp = query(func_in['sql'])
                else:
                    func_resp = "unknown function"
                
                input_list.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": func_resp # already json-encoded
                })
        
        if not called_function:
            break; # if no function call, we can just return response

    return response.output_text

@d_client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(d_client))

@d_client.event
async def on_message(message):
    # don't respond to our own messages
    if message.author == d_client.user:
        return

    # only care if we are mentioned in the message
    if d_client.user not in message.mentions:
        return

    await message.add_reaction('⏳')  # Hourglass emoji
    await message.channel.send(answer_question(message.content))
    await message.add_reaction('✅')  # Check mark emoji
    await message.remove_reaction('⏳', d_client.user)

d_client.run(os.getenv('TOKEN'))




