# Streamlit libraries.
import streamlit as st
import streamlit.components.v1 as components

# Database connection library.
import snowflake.connector


# Data manipulation libraries.
import pandas as pd
import numpy as np

# Some misc libraries.
import datetime
import requests


# Title of the webpage.
st.title('Prototype: Explore edX Videos')


# Connect to Snowflake.
ctx = snowflake.connector.connect(
    user=st.secrets['DB_USERNAME'],
    password=st.secrets['DB_TOKEN'],
    account=st.secrets['info']['account'],
    warehouse=st.secrets['info']['warehouse'],
    database=st.secrets['info']['database'],
    role=st.secrets['info']['role'],
        )

cur = ctx.cursor()

# Prepare for fetching data.
sql = """select * from user_data.nrobertson.streamlit_video_data"""
cols = ['subject_name', 'course_key', 'courserun_key', 'display_name',
       'num_views', 'transcript_link', 'video_link', 'video_length_seconds',
       'video_transcript', 'partner', 'course_title', 'course_url',
       'image_url']

# Fetch data. Cache it so that it doesn't re-run everytime 
# you type something new in search.
@st.cache
def run_query(query=sql, columns=cols,replace=False):
    if replace!=False:
        query = query.replace('_____',replace)
        
    cur.execute(query)
    results = cur.fetchall()
    
    if len(results) > 0:
        arr = np.array(results)
        df = pd.DataFrame(arr, columns=columns)
        return df
    
    else:
        df = pd.DataFrame()
        return df

# Save fetched data in df.
df = run_query().sort_values(by='num_views',ascending=False)

# A short description on what the page is.
st.write("""
	A proof-of-concept prototype allowing a user to explore **{}** videos indexed from currently running edX courses.
	The search algorithm and search experience are rudimentary. It's minimally designed to allow someone to explore our videos.
	""".format(len(df)))


# A few (very lazily written) text styling functions. These could be easily
# condensed into one function if I bothered with regex.
def bold_words(string, search_term):
	result = ''
	for term in string.split():
		if term.lower() in search_term.lower().split():
			result += '<b><i><u>' + term + '</b></i></u> '
		else:
			result += term + ' '	

	return result

def period_breaks(string):
	result = ''
	for term in string.split('.'):
		result += term + '.<br><br>'
	return result[:-9]

def question_breaks(string):
	result = ''
	for term in string.split('?'):
		result += term + '?<br><br>'
	return result[:-9]

def exclamation_breaks(string):
	result = ''
	for term in string.split('!'):
		result += term + '!<br><br>'
	return result[:-9]

# Where the user puts in their search term.
search_term = st.text_input(label='Enter search term here', value='data science')

# Search for a match on the search term in either the video's name or transcript.
if search_term:
	mask1 = df['display_name'].str.contains(search_term, case=False, na=False)
	mask2 = df['video_transcript'].str.contains(search_term, case=False, na=False)
	
	# Report how many videos found.
	st.header('{} results found.'.format(len(df[(mask1) | (mask2)])))

	st.write('Results sorted in descending order by most views.')

	# Print out each video, with a little context.
	count = 0
	for i, row in df[(mask1) | (mask2)].iterrows():

		# Pretty print video length.
		length = row['video_length_seconds']
		length = str(datetime.timedelta(seconds=length))

		count += 1

		col1, col2 = st.columns([1,3])

		# Col1 has context about the course.
		with col1:
			# Course image.
			st.image(row['image_url'], use_column_width=True)
			# Short description.
			st.write("""_This video is part of {}'s course '{}'._""".format(row['partner'], row['course_title']))
			# Button to take you to course about page.
			st.write('''
				<head>
			    <a target="_blank" href="{}">
			        <button style="color:D23227;background-color:#FFFFFF";border-color:#D23227>
			            See the course
			        </button>
			    </a>
			    '''.format(row['course_url']),
			    unsafe_allow_html=True
			)

		# Col2 has context about the video.
		with col2:
			# Video name.
			st.subheader('{}: {}'.format(count, row['display_name']))
			# Couple of video data points.
			st.text('est length: {} | views: {}'.format(length,row['num_views']))
			# Button to take you to the video.
			st.write('''
				<head>
			    <a target="_blank" href="{}">
			        <button style="color:white;background-color:#D23227";border-color:#D23227>
			            See Video on edX
			        </button>
			    </a>
			    '''.format(row['video_link']),
			    unsafe_allow_html=True
			)
			st.markdown('\n')
			# Print the tidy/pretty printed/scrollable transcript.
			st.markdown('**Transcript**')
			transcript = '{}'.format(str(row["display_name"]) +': <br><br>' + str(row['video_transcript']))
			transcript = bold_words(transcript, search_term=search_term)
			transcript = period_breaks(transcript)
			transcript = exclamation_breaks(transcript)
			transcript = question_breaks(transcript)
			transcript = '<style>:root {background-color: #F2F0EF;}</style>' + transcript
			components.html(transcript, height=300, scrolling=True)


