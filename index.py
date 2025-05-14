# Ensure version compatibility between bfabric_web_apps and bfabric_web_app_template.
# Both must be the same version to avoid compatibility issues.
# Example: If bfabric_web_apps is version 0.1.3, bfabric_web_app_template must also be 0.1.3.
# Verify and update versions accordingly before running the application.

from dash import Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
import bfabric_web_apps
from generic.callbacks import app
from generic.components import no_auth
from bfabric_web_apps import dataset_to_dictionary
import pandas as pd
from dash import dash_table
import os

# Here we define the sidebar of the UI, including the clickable components like dropdown and slider. 
sidebar = bfabric_web_apps.components.charge_switch + [
    html.Br(),
    html.P(id="sidebar_text_3", children="Submit job to which queue?"),  # Text for the input field.
    dcc.Dropdown(
        options=[
            {'label': 'local', 'value': 'local'},
            {'label': 'light', 'value': 'light'},
            {'label': 'heavy', 'value': 'heavy'},
        ],
        value='local',
        id='queue'
    ),
    html.Br(),
    dbc.Button('Submit', id='sidebar-button'),  # Button for user submission.
]

# here we define the modal that will pop up when the user clicks the submit button.
modal = html.Div([
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Ready to Prepare Create Workunits?")),
        dbc.ModalBody("Are you sure you're ready to create workunits?"),
        dbc.ModalFooter(dbc.Button("Yes!", id="Submit", className="ms-auto", n_clicks=0)),],
    id="modal-confirmation",
    is_open=False,),
])

# Here are the alerts which will pop up when the user creates workunits 
alerts = html.Div(
    [
        dbc.Alert("Success: Workunit created!", color="success", id="alert-fade-success", dismissable=True, is_open=False),
        dbc.Alert("Error: Workunit creation failed!", color="danger", id="alert-fade-fail", dismissable=True, is_open=False),
    ], style={"margin": "20px"}
)

# Here we define a Dash layout, which includes the sidebar, and the main content of the app. 
app_specific_layout = dbc.Row(
        id="page-content-main",
        children=[
            dcc.Loading(alerts), 
            modal,  # Modal defined earlier.
            dbc.Col(
                html.Div(
                    id="sidebar",
                    children=sidebar,  # Sidebar content defined earlier.
                    style={
                        "border-right": "2px solid #d4d7d9",
                        "height": "100%",
                        "padding": "20px",
                        "font-size": "20px",
                        "overflow-y":"scroll",
                        "overflow-x":"hidden",
                        "max-height":"65vh"
                    }
                ),
                width=3,  # Width of the sidebar column.
            ),
            dbc.Col(
                html.Div(
                    id="page-content",
                    children=[
                        html.Div(id="auth-div")  # Placeholder for `auth-div` to be updated dynamically.
                    ],
                    style={
                        "margin-top": "2vh",
                        "margin-left": "2vw",
                        "font-size": "20px",
                        "overflow-y":"scroll",
                        "overflow-x":"hidden",
                        "max-height":"65vh"
                    }
                ),
                width=9,  # Width of the main content column.
            ),
        ],
        style={"margin-top": "0px", "min-height": "40vh"}  # Overall styling for the row layout.
    )

# Here we define the documentation content for the app.
documentation_content = [
    html.H2("Welcome to Hello world nextflow!"),
    html.P(
        [
            "This is a hello world app, click around to your heart's content! "
        ]
    ),
]

app_title = "NFC hello world"  # Title of the app.

# here we use the get_static_layout function from bfabric_web_apps to set up the app layout.
app.layout = bfabric_web_apps.get_static_layout(                    # The function from bfabric_web_apps that sets up the app layout.
    base_title=app_title,                                           # The app title we defined previously
    main_content=app_specific_layout,                               # The main content for the app defined in components.py
    documentation_content=documentation_content,                    # Documentation content for the app defined in components.py
    layout_config={"workunits": True, "queue": True, "bug": True}   # Configuration for the layout
)

# This callback is necessary for the modal to pop up when the user clicks the submit button.
@app.callback(
    Output("modal-confirmation", "is_open"),
    [Input("sidebar-button", "n_clicks"), Input("Submit", "n_clicks")],
    [State("modal-confirmation", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    [
        Output("queue", "disabled"), 
        Output("sidebar-button", "disabled")
    ],
    [
        Input("token_data", "data"),
        Input("entity", "data"),
    ]
)
def disable_queue(token_data, entity_data):
    """
    This callback disables the queue and sidebar button if the token data is not available.
    """
    if token_data is None or entity_data is None:
        return True, True
    else:
        return False, False
    

@app.callback(
    Output("page-content", "children"),
    Input("entity", "data"),
)
def update_page_content(entity_data):
    if not entity_data:
        return no_auth
    else: 
        dataset_data = entity_data.get("full_api_response", {}) 
        if dataset_data:
            dataset_id = dataset_data.get("id", None)
            if dataset_id:
                # Convert the dataset to a dictionary
                dataset_dict = dataset_to_dictionary(dataset_data)
                # Create a DataFrame from the dictionary
                df = pd.DataFrame.from_dict(dataset_dict, orient="columns")
                # Create a Dash DataTable from the DataFrame
                table = dash_table.DataTable(
                    id="dataset-table",
                    columns=[{"name": str(i), "id": str(i)} for i in df.columns],
                    data=df.to_dict("records"),
                    sort_action="native",
                    sort_mode="multi",
                    row_deletable=False,
                    page_action="native",
                    page_current=0,
                    page_size=10,
                    style_table={'overflowX': 'auto', 'maxWidth': '90%'},
                    style_cell={'minWidth': '60px', 'width': '100px', 'maxWidth': '180px', 'whiteSpace': 'normal'},
                )
                
                return table
            else:
                return html.Div("Invalid Dataset.")
        else:
            return html.Div("No dataset found.")
    

@app.callback(
    [
        Output("alert-fade-success", "is_open"),
        Output("alert-fade-fail", "is_open")
    ],
    [
        Input("Submit", "n_clicks"),
    ],
    [
        State("queue", "value"),
        State("entity", "data"),
        State("token_data", "data"),
        State("app_data", "data"),
        State("url", "search")
    ], prevent_initial_call=True
)
def submit_job(n_clicks, queue, entity_data, token_data, app_data, raw_token):
    """
    This callback handles the creation of workunits when the user clicks the submit button.
    It will show success or failure alerts based on the outcome of the workunit creation.
    """

    # print("entity_data", entity_data)
    # print("app_data", app_data)

    if n_clicks:
        try: 
            
            files_as_byte_strings = {"attachment_1.html" : b"<html><body><h1>Hello World</h1></body></html>"}

            home_directory = os.path.expanduser("~") 
            
            bash_commands = [
                "echo 'hello world'", 
                f"nextflow run hello > {home_directory}/SCRATCH/hello.txt"
            ]

            container_id = entity_data.get("container", {}).get("id", 2220)

            resource_paths = {
                f"{home_directory}/SCRATCH/hello.txt": container_id,
            }

            attachment_paths = {
                "attachment_1.html": "attachment_1.html"
            }

            dataset_dict = {
                    str(container_id): {
                        "resources": ["hello.txt"],
                        "attachments": ["attachment_1.html"]
                    }
            }

            arguments = {
                "files_as_byte_strings": files_as_byte_strings,
                "bash_commands": bash_commands,
                "resource_paths": resource_paths, 
                "attachment_paths": attachment_paths,
                "token": raw_token,
                "service_id":bfabric_web_apps.SERVICE_ID,
                "charge": [container_id],
                "dataset_dict": dataset_dict,
            }
        

            if queue == "local":
                bfabric_web_apps.run_main_job(**arguments)
                
            else: 
                bfabric_web_apps.q(queue_name=queue).enqueue(
                    bfabric_web_apps.run_main_job,
                    kwargs=arguments
                )

            return True, False

        except Exception as e:
            print("Error creating workunit:", e)
            return False, True

# Here we run the app on the specified host and port.
if __name__ == "__main__":
    app.run(debug=bfabric_web_apps.DEBUG, port=bfabric_web_apps.PORT, host=bfabric_web_apps.HOST)

