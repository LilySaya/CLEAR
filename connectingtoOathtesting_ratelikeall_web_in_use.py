from flask import Flask, render_template, request, session, redirect, url_for
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


app = Flask(__name__)
app.secret_key = 'your_secret_key'

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

@app.route('/')

def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])

def submit():
    # Handle form data
    keywords = request.form['query']  # e.g., "rick, summer, morty"

    # Set default values for num_vid1, num_vid2, and num_vid3
    if 'num_vid1' not in session:
        session['num_vid1'] = 1 #Number of videos to like
    if 'num_vid2' not in session:
        session['num_vid2'] = 1 #Number of videos to add to watch later playlist
    if 'num_vid3' not in session:
        session['num_vid3'] = 0 #Number of channels to subscribe


    # num_videos = int(request.form['num_videos'])
    
    # Split keywords by commas and strip whitespace
    keyword_list = [keyword.strip() for keyword in keywords.split(',')]

    num_vid1 = session.get('num_vid1', None) 
    num_vid2 = session.get('num_vid2', None) 
    num_vid3 = session.get('num_vid3', None) 
    
    
    # Authenticate the user
    creds = authenticate()
    
    # Process each keyword
    for keyword in keyword_list:
        #number of videos to like
        video_ids_tolike = search_youtube(creds, keyword, num_vid1)
        if video_ids_tolike:
            for video_id in video_ids_tolike:
                like_video(creds, video_id)

        #number of videos to add to Watch Later Playlist
        video_ids_toadd = search_youtube(creds, keyword, num_vid2)
        if video_ids_toadd:
            for video_id in video_ids_toadd:
                like_video(creds, video_id) #CHANGE THIS PLEASE
        
        #number of channels to subscribe
        #Please complete this using variable "num_vid3" (number of channels to subscribe)
    
    session.clear()
    return f"""Search for keywords '{', '.join(keyword_list)}' completed. So far, ...
                                            ...{num_vid1} videos have been liked and ...
                                            ...{num_vid2} videos have been added to Watch Later Playlist and ...
                                            ...{num_vid3} channels have been subscribed."""

@app.route('/options', methods=['GET','POST'])

def options():

    # Set default values if session is empty (first-time visit)
    if 'checkbox1' not in session:
        session['checkbox1'] = True
    if 'checkbox2' not in session:
        session['checkbox2'] = True
    if 'checkbox3' not in session:
        session['checkbox3'] = False
    if 'num_vid1' not in session:
        session['num_vid1'] = 1
    if 'num_vid2' not in session:
        session['num_vid2'] = 1
    if 'num_vid3' not in session:
        session['num_vid3'] = 0


    if request.method == 'POST':
        session['checkbox1'] = request.form.get('checkbox1') 
        session['checkbox2'] = request.form.get('checkbox2') 
        session['checkbox3'] = request.form.get('checkbox3') 

        if 'checkbox1' not in request.form:
            session['num_vid1'] = 0
        if 'checkbox2' not in request.form:
            session['num_vid2'] = 0
        if 'checkbox3' not in request.form:
            session['num_vid3'] = 0
        
        # If checkbox1 is checked, store the corresponding num_vid1 value
        if 'checkbox1' in request.form:
            num_vid1 = request.form.get('num_vid1',session['num_vid1'])  # Default to 0 if no value is provided
            session['num_vid1'] = num_vid1
        
        # If checkbox2 is checked, store the corresponding num_vid2 value
        if 'checkbox2' in request.form:
            num_vid2 = request.form.get('num_vid2',session['num_vid2']) # Default to 0 if no value is provided
            session['num_vid2'] = num_vid2
        
        # If checkbox3 is checked, store the corresponding num_vid3 value
        if 'checkbox3' in request.form:
            num_vid3 = request.form.get('num_vid3',session['num_vid3'])  # Default to 0 if no value is provided
            session['num_vid3'] = num_vid3

        return redirect(url_for('options')) 


    return render_template('options.html',num_vid1=session['num_vid1'],
                           num_vid2=session['num_vid2'],num_vid3=session['num_vid3'],
                           checked_value1=session['checkbox1'], checked_value2=session['checkbox2'],
                           checked_value3=session['checkbox3'])


def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        "./json_keys/client_secret_myproject20250117_desktop.json", SCOPES
    )
    credentials = flow.run_local_server(port=0)
    print("Authentication successful!")
    return credentials

def search_youtube(credentials, query, num_videos):
    youtube = build("youtube", "v3", credentials=credentials)
    video_ids = []
    next_page_token = None

    while len(video_ids) < num_videos:
        request = youtube.search().list(
            part="snippet",
            q=query,
            maxResults=min(num_videos - len(video_ids), 50),  # Fetch up to 50 results per page
            type="video",  # Ensure only videos are returned
            pageToken=next_page_token,
        )
        response = request.execute()

        for item in response.get("items", []):
            video_title = item["snippet"]["title"]
            video_id = item["id"].get("videoId")
            if video_id != "N/A":
                video_ids.append(video_id)
                print(f"Video {len(video_ids)}: {video_title}")
                if len(video_ids) == num_videos:
                    break

        # Check if there's another page of results
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return video_ids


def like_video(credentials, video_id):
    youtube = build("youtube", "v3", credentials=credentials)
    try:
        youtube.videos().rate(id=video_id, rating="like").execute()
    except HttpError as e:
        error_content = e.content.decode("utf-8")
        if "quotaExceeded" in error_content:
            print("Quota exceeded! Stopping further requests.")
            raise


if __name__ == "__main__":
    app.run(debug=True)


