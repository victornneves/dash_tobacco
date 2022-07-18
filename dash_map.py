import dash
from dash import html, dash_table
import dash_leaflet as dl
import matplotlib.path as mpath
import pandas as pd

from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate

MAP_ID = "map-id"
POLYLINE_ID = "polyline-id"
POLYGON_ID = "polygon-id"


df = pd.read_csv("input/Estrutura_406_Atual.csv", encoding = "ISO-8859-1").dropna().rename(columns={
  'Latitude - GD': "lat",
  "Longitude - GD": "lng"
})
df['contains'] = True
df.lat = df.lat.str.replace(",", ".").astype(float)
df.lng = df.lng.str.replace(",", ".").astype(float)
df = df[~df.lat.isin([0, -28.0, -29.0, -49.0])]
columns = ["ï»¿Nome do produtor", "Id. Orientador", "Vol. contrato atual (kg)",	"Ha. reg."]

POLY_DF = df

colors = [
 'red',
 'blue',
 'green',
 'yellow',
 'cyan',
 'magenta',
 '#81b1d2',
 '#56B4E9',
 '#E24A33',
 '#0072B2',
 '#f0f0f0',
]
colormap = dict(zip(df["Id. Orientador"].unique(), range(df["Id. Orientador"].unique().shape[0])))
df['color'] = df["Id. Orientador"].apply(lambda x: colors[colormap[x]])

markers = [
    dl.CircleMarker(center=(df.lat.iloc[i], df.lng.iloc[i]), radius=6, fillOpacity=0.8, color=df.color.iloc[i])
    for i in range(df.shape[0])
]

dummy_pos = [0, 0]
dlatlon2 = 1e-3  # Controls tolerance of closing click

app = dash.Dash()

app.layout = html.Div(children=[
    html.Div([
        dl.Map(id=MAP_ID, center=[-29.20819, -49.8295], zoom=8, children=[
            dl.TileLayer(),  # Map tiles, defaults to OSM
            dl.Polyline(id=POLYLINE_ID, positions=[dummy_pos]),  # Create a polyline, cannot be empty at the moment
            dl.Polygon(id=POLYGON_ID, positions=[dummy_pos]),  # Create a polygon, cannot be empty at the moment
            dl.LayerGroup(markers),
        ], style={'width': '100%', 'height': '500px'}),
    ]),
    html.Div(
        dash_table.DataTable(
            id='table2',
            columns=[{"name": i, "id": i} for i in ["Metric", "Value"]],
            data=[{"Metric" : "Soma Vol.", "Value": df['Vol. contrato atual (kg)'].sum()}],
            style_cell=dict(textAlign='left'),
            style_header=dict(backgroundColor="paleturquoise"),
            style_data=dict(backgroundColor="lavender")
        ), 
    ),
    html.Div(
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} 
                    for i in columns],
            data=df[columns].to_dict('records'),
            style_cell=dict(textAlign='left'),
            style_header=dict(backgroundColor="paleturquoise"),
            style_data=dict(backgroundColor="lavender")
        ), 
    )
])


def update_poly_df(polygon):
    path = mpath.Path(polygon)
    path.contains_points([[df.iloc[0].lat, df.iloc[0].lng]])
    df['contains'] = path.contains_points([[df.lat.iloc[i], df.lng.iloc[i]] for i in range(df.shape[0])])

def update_metric_table():
    return [{"Metric" : "Soma Vol.", "Value": df[df.contains]['Vol. contrato atual (kg)'].sum()}]

@app.callback([
    Output(POLYLINE_ID, "positions"),
    Output(POLYGON_ID, "positions"),
    Output("table", "data"),
    Output("table2", "data"),
],
[
    Input(MAP_ID, "click_lat_lng")
],
[
    State(POLYLINE_ID, "positions")
])
def update_polyline_and_polygon(click_lat_lng, positions):
    if click_lat_lng is None or positions is None:
        raise PreventUpdate()
    # On first click, reset the polyline.
    if len(positions) == 1 and positions[0] == dummy_pos:
        return [click_lat_lng], [dummy_pos], df[df.contains][columns].to_dict('records'), update_metric_table()
    # If the click is close to the first point, close the polygon.
    dist2 = (positions[0][0] - click_lat_lng[0]) ** 2 + (positions[0][1] - click_lat_lng[1]) ** 2
    if dist2 < dlatlon2:
        update_poly_df(positions)
        print(positions)
        return [dummy_pos], positions, df[df.contains][columns].to_dict('records'), update_metric_table()
    # Otherwise, append the click position.
    positions.append(click_lat_lng)
    return positions, [dummy_pos], df[df.contains][columns].to_dict('records'), update_metric_table()


if __name__ == '__main__':
    app.run_server(debug=True)