import plotly.express as px
from plotly.subplots import make_subplots
import altair as alt
import streamlit as st


def plot_freq_pie(df, title="Donut Chart", col_scale="Viridis", style="simple_white"):

  df.sort_values(by=["Counts"], ascending=False, inplace=True)
  if st.session_state.max_codes_slider_value < df.shape[0]:
    df = df.head(st.session_state.max_codes_slider_value)
  df["Codes"] = df["Codes"].apply(lambda x: x[:st.session_state.max_length_int] + ".."
                                  if isinstance(x, str) and len(x) > st.session_state.max_length_int else x)

  n_cols = df.shape[0]
  colors = px.colors.sample_colorscale(col_scale, [n / (n_cols - 1) for n in range(n_cols)])
  fig = px.pie(df, values="Counts", names="Codes", title=title, color_discrete_sequence=colors,
               hole=0.4, labels="inside", template=style)
  fig.update_layout(title_x=0.5)
  fig.update_traces(textposition="inside")
  fig.update_layout(uniformtext_minsize=12, uniformtext_mode="hide")
  fig.update_traces(pull=0.01)
  return fig


def plot_altair_freq_pie(source, title="Donut Chart", col_scale="Viridis", style="simple_white"):

  # source = pd.DataFrame({
  #   'category': ['A', 'B', 'C', 'D'],
  #   'value': [20, 30, 15, 35]
  # })

  if st.session_state.max_codes_slider_value < source.shape[0]:
    source = source.head(st.session_state.max_codes_slider_value)
  source['Code Names'] = source['Codes']
  source['Codes'] = source['Codes'].apply(lambda x: x[:st.session_state.max_length_int] + ".."
                                          if isinstance(x, str) and len(x) > st.session_state.max_length_int else x)

  custom_domain=source['Codes']
  n_cols = source.shape[0]
  custom_colors = px.colors.sample_colorscale(col_scale, [n / (n_cols - 1) for n in range(n_cols)])

  selector = alt.selection_point(on='click', empty='none', fields=['Codes', 'Counts', "attId", "setId"],toggle=True,)

  chart = alt.Chart(source).mark_arc(innerRadius=50).encode(
    theta='Counts:Q',
    color=alt.Color(
      'Codes:N',
      scale=alt.Scale(domain=custom_domain, range=custom_colors),
      legend=alt.Legend(title="Legend",symbolLimit=20,)
    ),
    #opacity=alt.condition(selector, alt.value(1), alt.value(0.3)),  # Highlight selected, fade others
    stroke=alt.condition(selector, alt.value('black'), alt.value(None)),  # Stroke outline if selected
    strokeWidth=alt.condition(selector, alt.value(2), alt.value(0)),  # Width of stroke
    text=alt.Text('Codes:N'),
    tooltip=['Code Names', 'Counts:Q']
  ).add_params(selector).properties(
    title=title  # Set your desired title here
)

  # Display the chart in Streamlit
  # event = st.altair_chart(chart, on_select="rerun")

  return chart


def plot_freq_bar(df, title="Bar Chart", col_scale="Viridis", style="simple_white",
                  x_axis="Codes", y_axis="Counts", plot_attributes=True):

  df.sort_values(by=[y_axis], ascending=False, inplace=True)
  if st.session_state.max_codes_slider_value < df.shape[0]:
    df = df.head(st.session_state.max_codes_slider_value)
  df[x_axis] = df[x_axis].apply(lambda x: x[:st.session_state.max_length_int] + ".."
                                if isinstance(x, str) and len(x) > st.session_state.max_length_int else x)

  n_cols = df.shape[0]
  colors = px.colors.sample_colorscale(col_scale, [n / (n_cols - 1) for n in range(n_cols)])
  if plot_attributes:
    fig = px.bar(df, y=y_axis, x=x_axis, color=x_axis, hover_data=[x_axis, y_axis, "attId", "setId"], title=title,
                 color_discrete_sequence=colors, labels="inside", template=style)
  else:
    fig = px.bar(df, y=y_axis, x=x_axis, color=x_axis, hover_data=[x_axis, y_axis], title=title,
                 color_discrete_sequence=colors, labels="inside", template=style)
  fig.update_layout(title_x=0.5)
  return fig


def plot_subplot_bar(df, title="Bar Chart", col_scale="Viridis", style="simple_white", subject="Codes"):

  df.sort_values(by=["Counts"], ascending=False, inplace=True)
  n_cols = df.shape[0]
  colors = px.colors.sample_colorscale(col_scale, [n / (n_cols - 1) for n in range(n_cols)])

  categories = []
  for i, row in df.iterrows():
    categories.append({subject: row[subject], "Counts": row["Counts"],
                       #"SetId": row["setId"], "AttributeId": row["attId"]
                       })

  subplots = make_subplots(
    rows=len(categories),
    cols=1,
    subplot_titles=[x[subject] for x in categories],
    shared_xaxes=True,
    print_grid=False,
    vertical_spacing=(0.45 / len(categories)),
  )
  _ = subplots['layout'].update(
    width=550,
  )
  for k, x in enumerate(categories):
    subplots.add_trace(dict(
      type='bar',
      orientation='h',
      y=[x[subject]],
      x=[x["Counts"]],
      text="N= {}".format(x["Counts"]),
      #text=["attributeId: {}, setId: {}".format(x["AttributeId"], x["SetId"])],
      hoverinfo='text',
      textposition='auto',
      marker=dict(
        color=colors[k],
      ),
    ), k + 1, 1)

    subplots['layout'].update(
      showlegend=False,
    )
    for x in subplots["layout"]['annotations']:
      x['x'] = 0
      x['xanchor'] = 'left'
      x['align'] = 'left'
      x['font'] = dict(
        size=12,
      )

    for axis in subplots['layout']:
      if axis.startswith('yaxis') or axis.startswith('xaxis'):
        subplots['layout'][axis]['visible'] = False
    subplots['layout']['margin'] = {
      'l': 0,
      'r': 0,
      't': 20,
      'b': 1,
    }
    height_calc = 45 * len(categories)
    height_calc = max([height_calc, 350])
    subplots['layout']['height'] = height_calc
    subplots['layout']['width'] = height_calc

  # n_cols = df.shape[0]
  # colors = px.colors.sample_colorscale(col_scale, [n / (n_cols - 1) for n in range(n_cols)])
  # fig = px.bar(df, y='Counts', x='Codes',color='Codes', title=title, color_discrete_sequence=colors,
  #              labels='inside', template=style)
  # fig.update_layout(title_x=0.5)

  return subplots

# def test_me():
#   data={'Supervised': 1495, 'Generative': 929, 'Not specified': 8684, 'None of the above': 379}
#   df=pd.DataFrame()
#   df["Codes"]=data.keys()
#   df["Counts"]=data.values()
#
#   st.session_state.max_codes_slider_value=10
#   st.session_state.max_length_int=20
#
#   fig= plot_freq_bar(df, title="Bar Chart", col_scale="Viridis", style="simple_white")
#   fig.show()
#
# test_me()
