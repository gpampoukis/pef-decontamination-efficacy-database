from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import os

app = Dash(__name__, title="PEF decontamination efficacy")

server = app.server

# Load your dataset
script_dir = os.path.dirname(os.path.abspath(__file__))
excel_file_path = os.path.join(script_dir, "20250509_pef_database_v01.xlsx")
df = pd.read_excel(excel_file_path, sheet_name='PEFInactivationData')

# Rename the columns
df.rename(columns={
    'est_energy_input_2_J_ml': 'Volumetric energy input (kJ/L)',
    'reduction_used_for_modelling': 'Decimal microbial reduction (-)',
    'matrix_category': 'Matrix category',
    'doi': 'DOI',
    'food_pH': 'Food pH',
    'organism_grouped': 'Microorganism',
    'food_product': 'Specific matrix'
}, inplace=True)

#print "NA" where pH value is missing
df['Food pH'] = df['Food pH'].fillna("NA")

# Convert 'actual_processing_temp_degree_cal' to numeric
df['Volumetric energy input (kJ/L)'] = pd.to_numeric(df['Volumetric energy input (kJ/L)'])
df['Decimal microbial reduction (-)'] = pd.to_numeric(df['Decimal microbial reduction (-)'])
    
# Define and apply filters
df = df[df['Volumetric energy input (kJ/L)'].notna()]
df = df[df['Volumetric energy input (kJ/L)'] <= 300]  
df = df[df['Decimal microbial reduction (-)'].notna()]
df = df[df['study_below_equal_300'] == 'yes']  

# Extract unique values
organism_grouped_values = df['Microorganism'].unique() if 'Microorganism' in df.columns else []
matrix_category_values = df['Matrix category'].unique() if 'Matrix category' in df.columns else []
#matrix_acidity_values = df['matrix_acidity'].unique() if 'matrix_acidity' in df.columns else []

# Define rounded min and max values for the Volumetric energy input (kJ/L) slider
min_est_energy_input_2_J_ml_rounded = round(df['Volumetric energy input (kJ/L)'].min(), 1)
max_est_energy_input_2_J_ml_rounded = round(df['Volumetric energy input (kJ/L)'].max(), 1)

# Define the layout of the Dash application
app.layout = html.Div([
    html.H4('Interactive plotting of PEF decontamination efficacy'),

    dcc.Graph(id="scatter-plot"),

    # Slider for filtering by Volumetric energy input (kJ/L)
    html.P("Filter by volumetric energy input (kJ/L)"),
    dcc.RangeSlider(
        id='Volumetric energy input (kJ/L)-range-slider', 
        min=min_est_energy_input_2_J_ml_rounded, 
        max=max_est_energy_input_2_J_ml_rounded, 
        value=[min_est_energy_input_2_J_ml_rounded, max_est_energy_input_2_J_ml_rounded]
    ),

    # Dropdown for selecting matrix category values
    html.P("Select matrix category:"),
    dcc.Dropdown(
        id='Matrix category-dropdown', 
        options=[{'label': i, 'value': i} for i in matrix_category_values], 
        value=matrix_category_values[0],
        multi=True
    ),

    # Dropdown for selecting Microorganism values
    html.P("Select microbial species:"),
    dcc.Dropdown(
        id='Microorganism-dropdown', 
        options=[{'label': i, 'value': i} for i in organism_grouped_values], 
        value=organism_grouped_values[0],
        multi=True
    )
])


@app.callback(
    Output("scatter-plot", "figure"), 
    [
        #Input("Food pH-range-slider", "value"), 
        Input("Volumetric energy input (kJ/L)-range-slider", "value"),
        Input("Matrix category-dropdown", "value"),
        #Input("matrix_acidity-dropdown", "value"),
        Input("Microorganism-dropdown", "value")
    ]
)
def update_bar_chart(est_energy_input_2_J_ml_range,
                     selected_matrix_categories, 
                     selected_organism_grouped):
    """
    Updates the scatter plot based on the selected filters.
    """

    # Rounding Volumetric energy input (kJ/L) for filtering
    rounded_area_values = df['Volumetric energy input (kJ/L)'].round(1)
    rounded_area_range = [
        round(est_energy_input_2_J_ml_range[0], 1), 
        round(est_energy_input_2_J_ml_range[1], 1)
    ]
    
    mask = (
        #(df['Food pH'].between(*Food pH_range) | df['Food pH'].isna()) &
        rounded_area_values.between(*rounded_area_range) &
        df['Matrix category'].isin(
            selected_matrix_categories if isinstance(selected_matrix_categories, list) 
            else [selected_matrix_categories]
        ) &
        df['Microorganism'].isin(
            selected_organism_grouped if isinstance(selected_organism_grouped, list) 
            else [selected_organism_grouped]
        )
    )

    filtered_df = df[mask]
    
    # Manually define symbol and color sequences to ensure distinct markers & colors
    symbol_sequence = [
        'circle', 'square', 'diamond', 'triangle-up', 'triangle-down',
        'cross', 'x', 'star-triangle-up', 'hexagon', 'star'
    ]
    color_sequence = px.colors.qualitative.Dark24

    # Create the scatter plot with manual symbol and color sequences
    fig = px.scatter(
        filtered_df,
        x="Volumetric energy input (kJ/L)",
        y="Decimal microbial reduction (-)",
        symbol="Matrix category",
        color="DOI",
        hover_data=['Volumetric energy input (kJ/L)', 'Food pH', 'Matrix category', 
                    'Microorganism', 'Specific matrix'],
        symbol_sequence=symbol_sequence,
        color_discrete_sequence=color_sequence,
        trendline="ols",
        trendline_scope="overall",   # Single linear fit across all data
        trendline_color_override="black",  # Optional: make the trendline black
        trendline_options={"add_constant": False}
    )

    # Update axis titles
    fig.update_layout(
        xaxis_title="Volumetric energy input (kJ/L)",
        yaxis_title="Decimal microbial reduction (-)"
    )
   
    return fig


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))   # Render injects PORT
    app.run_server(host="0.0.0.0", port=port, debug=False)
