import folium
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_folium import st_folium
df = pd.read_csv("Crime_Data_updated.csv")
st.title("Los Angeles Crime Data (2020-2023)")
df.isna().sum()
df = df.dropna(subset=['victim_sex'])
df = df.dropna(subset=['weapon_description'])
df['date_occurred'] = pd.to_datetime(df['date_occurred'], errors='coerce')
df['month'] = df['date_occurred'].dt.month
df['year'] = df['date_occurred'].dt.year

st.sidebar.title("Filters")

selected_months = st.sidebar.multiselect(
    "Select Month(s) to View Crime Trend:",
    options=list(range(1, 13)),
    default=list(range(1, 13))
)
# Filter: Area
areas = df['area_name'].unique()
selected_areas = st.sidebar.multiselect(
    "Select Area(s):",
    options=areas,
    default=areas
)# Filter: Age Group
bins = [0, 18, 35, 50, 100]
labels = ['0-18', '19-35', '36-50', '51+']
df['age_group'] = pd.cut(df['victim_age'], bins=bins, labels=labels)
age_groups = df['age_group'].cat.categories
selected_age_groups = st.sidebar.multiselect(
    "Select Age Group(s):",
    options=age_groups,
    default=age_groups
)
# Filter: Weapon Type
top_weapons = df['weapon_description'].value_counts().head(10).index
selected_weapons = st.sidebar.multiselect(
    "Select Weapon(s):",
    options=top_weapons,
    default=top_weapons
)
# Apply Filters
filtered_df = df[
    (df['month'].isin(selected_months)) &
    (df['area_name'].isin(selected_areas)) &
    (df['age_group'].isin(selected_age_groups)) &
    (df['weapon_description'].isin(selected_weapons))
]
st.header("Crime Trend Over Months")

# Group data by month and count crimes
monthly_crimes = filtered_df.groupby(['year', 'month']).size().reset_index(name='crime_count')

# Pivot the data to get a proper structure for plotting
monthly_crimes_pivot = monthly_crimes.pivot(index='month', columns='year', values='crime_count').fillna(0)
st.line_chart(monthly_crimes_pivot)
st.write("This chart shows the number of crimes reported in each month over the selected years.")

#Area wise crimes
st.header("Crime Distribution by Area")
area_crimes = filtered_df['area_name'].value_counts().reset_index()
area_crimes.columns = ['Area Name', 'Crime Count']
norm = plt.Normalize(area_crimes['Crime Count'].min(), area_crimes['Crime Count'].max())
colors = plt.cm.viridis(norm(area_crimes['Crime Count']))
plt.figure(figsize=(10, 6))
plt.bar(area_crimes['Area Name'], area_crimes['Crime Count'], color=colors)
plt.xticks(rotation=90)
plt.title('Crime Distribution by Area', fontsize=16)
plt.xlabel('Area', fontsize=14)
plt.ylabel('Crime Count', fontsize=14)
st.pyplot(plt)
# Section: Age-Wise Crime Distribution
st.header("Age-Wise Crime Distribution")
age_crime_counts = filtered_df['age_group'].value_counts().reset_index()
age_crime_counts.columns = ['Age Group', 'Crime Count']
plt.figure(figsize=(8, 5))
plt.bar(age_crime_counts['Age Group'], age_crime_counts['Crime Count'], color='skyblue')
plt.title('Age-Wise Crime Distribution', fontsize=16)
plt.xlabel('Age Group', fontsize=14)
plt.ylabel('Number of Crimes', fontsize=14)
st.pyplot(plt)
# Section: Weapon-Wise Crime Distribution 
st.header("Weapon-Wise Crime Distribution")

# Get top 10 weapon types used in crimes
weapon_crimes = filtered_df['weapon_description'].value_counts().head(10)

# Create a horizontal bar chart for better label alignment
plt.figure(figsize=(12, 8))
weapon_crimes.plot(kind='barh', color='crimson')

# Set chart title and labels
plt.title('Top 10 Weapon Types Used in Crimes', fontsize=16)
plt.xlabel('Number of Crimes', fontsize=14)
plt.ylabel('Weapon Type', fontsize=14)

# Adjust label spacing
plt.tight_layout()

# Display the plot in Streamlit
st.pyplot(plt)

#Section: Crime Frequency Map
st.header("Crime Frequency Map")

# Function to get color based on crime frequency
def get_color(frequency):
    return {'high': 'red', 'medium': 'orange', 'low': 'green'}.get(frequency, 'green')

# Check if filtered data is valid
if filtered_df.empty or 'area_name' not in filtered_df.columns:
    st.error("Filtered DataFrame is empty or missing 'area_name' column.")
else:
    # Calculate crime counts and thresholds
    crime_counts = filtered_df['area_name'].value_counts()
    high_threshold = crime_counts.quantile(0.67)
    medium_threshold = crime_counts.quantile(0.33)

    # Assign crime frequency
    def get_crime_frequency(name):
        count = crime_counts.get(name, 0)
        if count >= high_threshold:
            return 'high'
        elif count >= medium_threshold:
            return 'medium'
        return 'low'

    filtered_df['crime_frequency'] = filtered_df['area_name'].apply(get_crime_frequency)

    # Map setup
    center_lat, center_lon = filtered_df[['latitude', 'longitude']].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # Add crime frequency markers to map
    for name, group in filtered_df.groupby('area_name'):
        coords = group[['latitude', 'longitude']].mean().values.tolist()
        folium.Circle(
            location=coords,
            radius=700,
            color=get_color(group['crime_frequency'].iloc[0]),
            fill=True,
            fill_color=get_color(group['crime_frequency'].iloc[0]),
            fill_opacity=0.6
        ).add_to(m)

    st_folium(m, width=800, height=500)

    # Add legend
    st.markdown("""
        <div style="border: 2px solid grey; padding: 10px; background-color: white; display: inline-block;">
            <strong>Crime Frequency Legend</strong><br>
            <span style="color: red;">⬤</span> High Crimes<br>
            <span style="color: orange;">⬤</span> Medium Crimes<br>
            <span style="color: green;">⬤</span> Low Crimes
        </div>
    """, unsafe_allow_html=True)
# Add attribution at the end
st.markdown("""
    <div style="text-align:center; padding:10px;">
        <strong>Project by Haritha Vijjapu</strong>
    </div>
""", unsafe_allow_html=True)
# Adding a page for Key Insights
page = st.sidebar.radio("Select a Page", ["Data Overview", "Key Insights"])

if page == "Key Insights":
    st.header("Key Insights of Crime Data")

    # Example Key Insights
    st.write("Here are some key insights derived from the data:")

    # You can present insights based on data analysis:
    st.write("- **Crime Hotspots**: Areas with the top 4 highest frequency of crimes are 77th Street,Central,Southeast,Southwest.")
    st.write("- **Weapon Usage**: Top Weapon on Trend is Strong Arm.")
    st.write("- **Victim Age Groups**: The most effected crime victims are of age group between 19-35.")
    st.write("- **Temporal Trends**: Monthly and yearly variations in crime occurrences.")
    st.write("- **Crime Frequency**: Crime distribution based on frequency (high, medium, low).")

   