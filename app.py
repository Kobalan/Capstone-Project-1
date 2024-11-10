#1)Libraries
from googleapiclient.discovery import build
import pandas as pd
import re
import mysql.connector
import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components



#---------------------------------------------------------------------------
#2) Page Configuration
st.set_page_config(page_title="Capstone_Project",
                   layout= "wide",
                   initial_sidebar_state= "expanded")
                   
st.sidebar.image('Youtube_logo.jpg', width=400)

hide_streamlit_style = """ <html> <body><h1 style="font-family:Google Sans; color:blue;font-size:40px"> About this Project </h1>
        <p style="font-family:Google Sans; font-size:20px">
        <b>Project_Title</b>: <br>Youtube Data Harvesting and Warehousing <br>
        <b>Technologies_Used</b> :<br> Pandas,Google API, Streamlit, Mysql <br>
        <b>Domain </b> :Social Media <br>
        <b>Problem Statement:</b>: <br>The problem statement is to create a Streamlit application that allows users to access and analyze data from multiple YouTube channels.<br>
        <b>Author</b> : M.KOBALAN <br>
        <b>Linkedin</b> :https://www.linkedin.com/in/kobalan-m-106267227/
        </p>
        </body>  </html>  """
st.sidebar.markdown(hide_streamlit_style, unsafe_allow_html=True)


#-----------------------------------------------------------------------------

Col1,Col2=st.columns(2 )
with Col1:
    components.html("""<html><body"><h1 style="font-family:Google Sans; font-size:50px">Youtube History</h1></body></html>""")
    st.image('about.jpg')
    st.image('about2.jpg')
    components.html("""<html><body"><h1 style="font-family:Google Sans; font-size:50px">Youtube Revenue</h1></body></html>""")
    st.image('revenue.jpg')
with Col2:
    components.html("""<html><body"><h1 style="font-family:Google Sans; font-size:50px">Youtube Business Model</h1></body></html>""",)
    st.image('about5.jpg')
    components.html("""<html><body"><h1 style="font-family:Google Sans; font-size:50px">Youtube Algorithm</h1></body></html>""")
    st.image('about6.jpg')

#3)Database Connection
#Creating or Connecting a Database in SQL....

database= mysql.connector.connect(host="localhost",user ="root",
  password ="kobalan",auth_plugin="mysql_native_password",database="youtube")
cursor=database.cursor()
    
#4)Creating Functions for retrieving needed data and inserting data into database

    #1]API_Connection...

api_key = 'AIzaSyBMJHpVbZCMo65P3qucFfKM9nhYx4_h67A' 
youtube = build("youtube", "v3", developerKey=api_key)
#Storing function in variable for reusable    


    #2]Getting Channel_Details using Channel_id......

def get_channelDetails(id):
    channel_id = id             
    request = youtube.channels().list(
        id=channel_id,
        part='snippet,statistics,contentDetails'
        )
    
    response = request.execute()                            
    for i in response['items']:
        data=dict(
                Channel_id=channel_id,
                Channel_Name=i['snippet']['title'],
                Channel_description=i['snippet']['description'],
                Subscription_Count=i['statistics']['subscriberCount'],
                Channel_Views=i['statistics']['viewCount'],
                Total_Video_Count=i['statistics']['videoCount'],
                Playlist_Id=i['contentDetails']['relatedPlaylists']['uploads']
              )
    return data


    #3]Getting Video IDs for retrieving Video_Details.......

def get_videoID(Channel_id):
    video_ids=[]
    request1 = youtube.channels().list(
            id=Channel_id,
            part='contentDetails')
    response1=request1.execute()
    playlist_ID=response1['items'][0]['contentDetails']['relatedPlaylists']['uploads']           #For getting Video IDs we need Channel_Playlist ID
    next_page_token=None
    while True:
              request2=youtube.playlistItems().list(
                      part='snippet',
                      playlistId=playlist_ID,
                      maxResults=50,
                      pageToken=next_page_token
                  )
              response2=request2.execute()
              for i in range(len(response2['items'])):
                  video_ids.append(response2['items'][i]['snippet']['resourceId']['videoId'])
              next_page_token=response2.get('nextPageToken')
              if next_page_token is None:
                break    
    return video_ids


    #4]Getting Video Details using Video_ID.....

def get_videoDetails(video_IDs):
    video_data=[]

    for video_id in video_IDs:
        request=youtube.videos().list(
            part="snippet,ContentDetails,statistics",
            id=video_id
        )
        
        response=request.execute()
        for item in response['items']:
                data=dict(
                    Channel_name = item['snippet']['channelTitle'],
                    Channel_id = item['snippet']['channelId'],
                    Video_ID=item['id'],
                    Video_name=item['snippet']['title'],
                    Tags=item['snippet'].get('tags'),        
                    Published_Date=item['snippet']['publishedAt'],                        
                    Views_Count=item['statistics']['viewCount'],
                    Likes_Count=item['statistics'].get('likeCount'),                                               
                    Favorite_Count=item['statistics']['favoriteCount'], 
                    Comment_Count=item['statistics']['commentCount'],
                    Duration=item['contentDetails']['duration'],
                    Thumbnail=item['snippet']['thumbnails']['default']['url'],
                    Caption_Status=item['contentDetails']['caption'],
                    Description=item['snippet']['description']
                    )
        video_data.append(data)
    return video_data

    #5]Getting Comment_Details using Video_ID....

def get_commentDetails(video_IDs):
    try:
        comment_data=[]
        for video_id in video_IDs:
            request=youtube.commentThreads().list(
                        part="snippet",
                        videoId=video_id
            )        
            response=request.execute()
            for item in response['items']:
                data=dict(
                        video_ID=item['snippet']['topLevelComment']['snippet']['videoId'],
                        Comment_ID=item['id'],
                        Comment_Text=item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        Comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        Comment_PublishedAt=item['snippet']['topLevelComment']['snippet']['publishedAt']
                        )
                comment_data.append(data)  
    except:
        pass              
    return comment_data

    #6]Creating Channel Table in SQL.... 

def  channel_Table(channel_ID):
    ch_List=[]
        #Creating Table for Channel_Details
    Channel_details = """CREATE TABLE  IF NOT EXISTS Channels(
                        Channel_name  VARCHAR(100),
                        Channel_id VARCHAR(50) primary key,
                        Subscribers INT ,
                        Views int,
                        Total_Videos int,
                        Channel_Description text,
                        Playlist_Id varchar(100)
                        )"""
    #  # SQL_table created
    cursor.execute(Channel_details)
    database.commit()

#Inserting values into SQL_table from dataFrame...
    
    channel_details=get_channelDetails(channel_ID)
    ch_List.append(channel_details)
    df_Channel_details=pd.DataFrame(ch_List)
    for index,row in df_Channel_details.iterrows():
        insert_values='''insert into Channels(Channel_name,
                        Channel_id,
                        Subscribers,
                        Views,
                        Total_Videos,
                        Channel_Description,
                        Playlist_Id)

                    values(%s,%s,%s,%s,%s,%s,%s)'''
        
        values=(row['Channel_Name'],
                row['Channel_id'],
                row['Subscription_Count'],
                row['Channel_Views'],
                row['Total_Video_Count'],
                row['Channel_description'],
                row['Playlist_Id'])
        cursor.execute(insert_values,values)
        database.commit()
  
def convert_duration(duration):
    regex = r'PT(\d+H)?(\d+M)?(\d+S)?'
    match = re.match(regex, duration)
    if not match:
        return '00:00:00'
    hours, minutes, seconds = match.groups()
    hours = int(hours[:-1]) if hours else 0
    minutes = int(minutes[:-1]) if minutes else 0
    seconds = int(seconds[:-1]) if seconds else 0
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return '{:02d}:{:02d}:{:02d}'.format(int(total_seconds / 3600), int((total_seconds % 3600) / 60),int(total_seconds % 60))


    #7]Creating Video Table in SQL.... 
def video_Table(channel_ID):                                                                                                                                                                                                                                                                         
    vi_List=[]
    #Creating Table for Video_Details
   
    Video_details = """CREATE TABLE  IF NOT EXISTS Videos(
                        Channel_id varchar(30),
                        Channel_name varchar(50),
                        video_ID varchar(30) primary key,
                        Video_name varchar(150),
                        Description text,                      
                        Published_Date text,                        
                        Views_Count bigint,
                        Likes_Count bigint,    
                        Favorite_Count int, 
                        Comment_Count int,
                        Duration varchar(50),
                        Thumbnail varchar(200),
                        Caption_Status varchar(50)
                        )"""
    #  # SQL_table created
    cursor.execute(Video_details)
    database.commit()

    video_IDs=get_videoID(channel_ID)
    video_Details=get_videoDetails(video_IDs)
    for i in range(len(video_IDs)):
        vi_List.append(video_Details[i])
    df_Video_details=pd.DataFrame(vi_List)
    df_Video_details['Duration']=df_Video_details['Duration'].apply(lambda x: convert_duration(x))

    #Inserting values into SQL_table from dataFrame...
    for index,row in df_Video_details.iterrows():
        insert_values='''insert into videos (
                        Channel_id,
                        Channel_name,                         
                        video_ID,
                        Video_name,
                        Description,                 
                        Published_Date,                        
                        Views_Count,
                        Likes_Count,    
                        Favorite_Count, 
                        Comment_Count,
                        Duration,
                        Thumbnail,
                        Caption_Status)
                    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        
        values=(row['Channel_id'],
                row['Channel_name'],
                row['Video_ID'],
                row['Video_name'],
                row['Description'],
                row['Published_Date'],
                row['Views_Count'],
                row['Likes_Count'],
                row['Favorite_Count'],
                row['Comment_Count'],
                row['Duration'],
                row['Thumbnail'],
                row['Caption_Status']
                )       
        cursor.execute(insert_values,values)
        database.commit()

#8]Creating Comment Table in SQL....       
def comment_Table(channel_ID):
    cmt_List=[]
#Creating Table for Comment_Details

    Comment_details = """CREATE TABLE  IF NOT EXISTS Comments(
                    video_ID  VARCHAR(100),
                    Comment_ID VARCHAR(50) primary key,
                    Comment_Text text,
                    Comment_Author varchar(100),
                    Comment_PublishedAt text
                    
                    )"""
    # SQL_table created
    cursor.execute(Comment_details)
    database.commit()
  
    video_IDs=get_videoID(channel_ID)
    comment_Details=get_commentDetails(video_IDs)
    for i in range(len(comment_Details)):
        cmt_List.append(comment_Details[i])
    df_Comment_details=pd.DataFrame(cmt_List)

    #Inserting values into SQL_table from dataFrame...
    #Comment_PublishedAt
    for index,row in df_Comment_details.iterrows():
        insert_values='''insert into Comments(
                    video_ID,
                    Comment_ID,
                    Comment_Text,
                    Comment_Author,
                    Comment_PublishedAt
                    )
                    values(%s,%s,%s,%s,%s)'''
        
        values=(row['video_ID'],
                row['Comment_ID'],
                row['Comment_Text'],
                row['Comment_Author'],
                row['Comment_PublishedAt']
        )
        cursor.execute(insert_values,tuple(values))
        database.commit()
    
    #7] Creating functions for Showing table data
def Channel_opt():
    cursor.execute("""SELECT * FROM channels""")
    df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
    return st.table(df)
def Video_opt():
    cursor.execute("""SELECT * FROM videos""")
    df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
    return st.table(df)
def Comment_opt():
    cursor.execute("""SELECT * FROM comments""")
    df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
    return st.table(df) 
     

#5)Transforming Menu

components.html("""<html><body"><h1 style="font-family:Neutro; font-size:50px"><b>TRANSFORMATION</b></h1></body></html>""")
components.html("""<html><body"><h1 style="font-family:Google Sans; font-size:40px">Paste a Channel ID</h1>
                <p style="font-family:Google Sans; font-size:20px"><b>HINT: Visit(www.youtube.com)--> Go To Channel's Page-->About-->Click 'Share' button--> Click 'Copy ChannelID'</b><br>                </p>
                </body></html>""")
col3,col4=st.columns(2)
with col3:
    channel_ID=st.text_input('ID',label_visibility='hidden')

button=st.button(":blue[𝑻𝒓𝒂𝒏𝒔𝒇𝒐𝒓𝒎]")
ch_IDs=[]
if button:
    with st.spinner('Please Wait for it...'):
        cursor.execute("""SELECT Channel_id FROM channels""")
        df = pd.DataFrame(cursor.fetchall())
        for i in range(len(df)):
            ch_IDs.append(df[0][i])  
        if len(channel_ID)==0:    
             st.info("Please Enter Channel_ID")    
        elif channel_ID in ch_IDs:
            st.error("Already Inserted")
        else:  
                      
            channel_Table(channel_ID)
            video_Table(channel_ID)
            comment_Table(channel_ID)
            st.success("Transformed to MySQL Successfully!!!")


#6)Viewing Menu
    

components.html("""<html><h1 style="font-family:Google Sans; font-size:40px">Select a Table to show</h1><p style="font-family:Google Sans; font-size:30px"><b>Choose One</b></p></html>""")
col5,col6=st.columns(2)
with col5:  
    res_View=st.selectbox("Option",options=('Click the table you want to see','Channel_Table','Video_Table','Comment_Table'),label_visibility='hidden')
button2=st.button(":blue[𝑺𝒉𝒐𝒘]")
if button2:
    if res_View=='Channel_Table':
        Channel_opt()
    elif res_View=='Video_Table':
        Video_opt()   
    elif res_View=='Comment_Table':
        Comment_opt()
#-------------------------------------------------------------------------


#7)FAQ
col7,col8=st.columns(2)
with col7:
    components.html("""<html><h1 style="font-family:Google Sans; font-size:40px">Frequently Asked Questions</h1>
                <p style="font-family:Google Sans; font-size:30px"><b>Choose One</b></p></html>""")

    questions = st.selectbox('option',
    ['Click the question that you would like to query',
    '1. What are the names of all the videos and their corresponding channels?',
    '2. Which channels have the most number of videos, and how many videos do they have?',
    '3. What are the top 10 most viewed videos and their respective channels?',
    '4. How many comments were made on each video, and what are their corresponding video names?',
    '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
    '6. What is the total number of likes for each video, and what are their corresponding video names?',
    '7. What is the total number of views for each channel, and what are their corresponding channel names?',
    '8. What are the names of all the channels that have published videos in the year 2022?',
    '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
    '10. Which videos have the highest number of comments, and what are their corresponding channel names?'],label_visibility='hidden')
            

    if questions == '1. What are the names of all the videos and their corresponding channels?':
        cursor.execute("""SELECT Video_name AS Video_Title, Channel_name AS Channel_Name FROM videos ORDER BY Channel_name""")
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
        st.write(df)

    elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
        cursor.execute("""SELECT Channel_name,Total_videos 
                            FROM channels
                            ORDER BY Total_videos DESC""")
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
        st.write(df)
        fig = px.bar(df,
                        x=cursor.column_names[0],
                        y=cursor.column_names[1],
                        orientation='v',
                        color=cursor.column_names[0]
                    )

        st.plotly_chart(fig,use_container_width=True)


    elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
        cursor.execute("""SELECT  Channel_Name,Video_Name,Views_Count
                            FROM videos
                            ORDER BY Views_Count DESC
                            LIMIT 10""")
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
        st.write(df)

        fig = px.bar(df,
                        x=cursor.column_names[2],
                        y=cursor.column_names[1],
                        orientation='h',
                        color=cursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)  

    elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
        cursor.execute("""SELECT Channel_name,Video_name,Comment_Count
                            FROM videos order by Comment_Count desc
                            """)
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
        st.write(df)

    elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
        cursor.execute("""SELECT Channel_Name,Video_name,Likes_Count 
                            FROM videos
                            ORDER BY Likes_Count DESC
                            LIMIT 10""")
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
        st.write(df)
        fig = px.bar(df,
                        x=cursor.column_names[2],
                        y=cursor.column_names[1],
                        orientation='h',
                        color=cursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)

    elif questions == '6. What is the total number of likes for each video, and what are their corresponding video names?':
        cursor.execute("""SELECT Video_name,Likes_Count
                            FROM videos
                            ORDER BY Likes_Count DESC""")
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
        st.write(df)

    elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
        cursor.execute("""SELECT Channel_Name,Views
                            FROM channels
                            ORDER BY Views DESC""")
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
        st.write(df)

        fig = px.bar(df,
                        x=cursor.column_names[0],
                        y=cursor.column_names[1],
                        orientation='v',
                        color=cursor.column_names[0]
                    )
        fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig,use_container_width=True)


    elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':
        cursor.execute("""SELECT channel_name,Video_name,published_Date FROM videos WHERE extract(year from published_date)=2022""")
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
        st.write(df)

    elif questions == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
        cursor.execute("""SELECT channel_name,SEC_TO_TIME(AVG(TIME_TO_SEC(Duration))) as Average_Duration FROM videos group by channel_name""")
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)           
        st.write(df)
        

    elif questions == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
        cursor.execute("""SELECT Channel_Name,Video_name,Comment_Count
                            FROM videos
                            ORDER BY Comment_Count DESC
                            LIMIT 20""")
        df = pd.DataFrame(cursor.fetchall(),columns=cursor.column_names)
        st.write(df)
        fig = px.bar(df,
                        x=cursor.column_names[1],
                        y=cursor.column_names[2],
                        orientation='v',
                        color=cursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)        
        


