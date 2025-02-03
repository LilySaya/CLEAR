from flask import Flask, render_template, request, session, redirect, url_for
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials 
import os
import json

app = Flask(__name__)
# No specific reason that I add this. ChatGPT ask me to do this. 
app.secret_key = os.urandom(24)

CLIENT_SECRETS_FILE = "json_keys/web/client_secret_YoutubeDataAPIv320250115_web.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
REDIRECT_URI = 'https://melnikov.tplinkdns.com/oauth2callback'

# Flow
def get_flow():
    with open(CLIENT_SECRETS_FILE) as f:
        client_config = json.load(f)
    
    return Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

@app.route('/')
def index():
    return render_template('index.html')

# Part of codes for requiring OAuth from user 
@app.route('/authorize')
def authorize():
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # 상태 값 세션 저장 (CSRF 방지)
    session['state'] = state
    
    return redirect(authorization_url)

# Part of codes for requiring OAuth from user 
@app.route('/oauth2callback', methods=['GET', 'POST'])
def oauth2callback():
    # 상태 값 검증
    if 'state' not in session:
        return 'state is not in the session', 400
    
    if session['state'] != request.args.get('state'):
        return 'state is not identical', 400

    # 인증 코드 교환
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)
    
    # 자격 증명 세션 저장
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    
    return redirect(url_for('submit_handler'))

# Logic is a bit changed so that we can request OAuth from user.
@app.route('/submit', methods=['GET', 'POST'])
def submit_handler():

    if 'credentials' not in session:
        session['query'] = request.form['query']
        return redirect(url_for('authorize'))
    
    credentials_data = session['credentials']
    credentials = Credentials(
        token=credentials_data['token'],
        refresh_token=credentials_data['refresh_token'],
        token_uri=credentials_data['token_uri'],
        client_id=credentials_data['client_id'],
        client_secret=credentials_data['client_secret'],
        scopes=credentials_data['scopes']
    )
    
    # 폼 데이터 처리
    if request.method == 'GET':
        keywords = session.pop('query')
    else:
        keywords = request.form['query']
    keyword_list = [keyword.strip() for keyword in keywords.split(',')]
    
    # 기본값 설정
    session.setdefault('num_vid1', 1)
    session.setdefault('num_vid3', 0)
    
    # 각 키워드 처리
    for keyword in keyword_list:
        # 비디오 좋아요 처리
        video_ids = search_youtube(credentials, keyword, session['num_vid1'])
        for video_id in video_ids:
            like_video(credentials, video_id)
        
        # 채널 구독 처리
        channel_ids = search_youtube_channels(credentials, keyword, session['num_vid3'])
        for channel_id in channel_ids:
            subscribe_to_channel(credentials, channel_id)
    
    session.clear()
    return f"""Search for keywords '{', '.join(keyword_list)}' completed. So far, ...
                                            ...{session['num_vid1']} videos have been liked and ...
                                            ...{session['num_vid3']} channels have been subscribed."""
    # return f"처리 완료: {', '.join(keyword_list)}"

@app.route('/options', methods=['GET','POST'])
def options():

    # Set default values if session is empty (first-time visit)
    if 'checkbox1' not in session:
        session['checkbox1'] = True
    #if 'checkbox2' not in session:
    #    session['checkbox2'] = True
    if 'checkbox3' not in session:
        session['checkbox3'] = False
    if 'num_vid1' not in session:
        session['num_vid1'] = 1
    #if 'num_vid2' not in session:
    #    session['num_vid2'] = 1
    if 'num_vid3' not in session:
        session['num_vid3'] = 0


    if request.method == 'POST':
        session['checkbox1'] = request.form.get('checkbox1') 
        #session['checkbox2'] = request.form.get('checkbox2') 
        session['checkbox3'] = request.form.get('checkbox3') 

        if 'checkbox1' not in request.form:
            session['num_vid1'] = 0
        #if 'checkbox2' not in request.form:
            #session['num_vid2'] = 0
        if 'checkbox3' not in request.form:
            session['num_vid3'] = 0
        
        # If checkbox1 is checked, store the corresponding num_vid1 value
        if 'checkbox1' in request.form:
            num_vid1 = request.form.get('num_vid1',session['num_vid1'])  # Default to 0 if no value is provided
            session['num_vid1'] = num_vid1
        
        # If checkbox2 is checked, store the corresponding num_vid2 value
        #if 'checkbox2' in request.form:
        #    num_vid2 = request.form.get('num_vid2',session['num_vid2']) # Default to 0 if no value is provided
        #    session['num_vid2'] = num_vid2
        
        # If checkbox3 is checked, store the corresponding num_vid3 value
        if 'checkbox3' in request.form:
            num_vid3 = request.form.get('num_vid3',session['num_vid3'])  # Default to 0 if no value is provided
            session['num_vid3'] = num_vid3

        return redirect(url_for('options')) 


    return render_template('options.html',num_vid1=session['num_vid1'],
                           num_vid3=session['num_vid3'],
                           checked_value1=session['checkbox1'],
                           checked_value3=session['checkbox3'])


# def authenticate():
#     flow = InstalledAppFlow.from_client_secrets_file(
#         "./json_keys/desktop/client_secret_YoutubeDataAPIv320250115_desktop.json", SCOPES
#     )
#     credentials = flow.run_local_server(port=0)
#     print("Authentication successful!")
#     return credentials

def authenticate():
    with open(CLIENT_SECRETS_FILE) as f:
        client_config = json.load(f)

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI  # Use Flask's redirect URI
    )

    return flow

### Sub functions for like starts here ### 
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
### Sub functions for like ends here ### 

### Sub functions for add to playlist starts here ### 
# def add_to_playlist(credentials, video_id, playlist_id):
#     youtube = build("youtube", "v3", credentials=credentials)
#     try:
#         request = youtube.playlistItems().insert(
#             part="snippet",
#             body={
#                 "snippet": {
#                     "playlistId": playlist_id,
#                     "resourceId": {
#                         "kind": "youtube#video",
#                         "videoId": video_id
#                     }
#                 }
#             }
#         )
#         response = request.execute()
#         print(f"Added video ID {video_id} to playlist ID {playlist_id}")
#         return response
#     except HttpError as e:
#         error_content = e.content.decode("utf-8")
#         if "quotaExceeded" in error_content:
#             print("Quota exceeded! Stopping further requests.")
#             raise
#         else:
#             print(f"Failed to add video to playlist: {error_content}")
### Sub functions for add to playlist ends here ### 

### Sub functions for subscribe the channel starts here ### 
def search_youtube_channels(credentials, query, num_channels):
    youtube = build("youtube", "v3", credentials=credentials)
    channel_ids = []
    next_page_token = None

    while len(channel_ids) < num_channels:
        request = youtube.search().list(
            part="snippet",
            q=query,
            maxResults=min(num_channels - len(channel_ids), 50),  # Fetch up to 50 results per page
            type="channel",  # Search for channels instead of videos
            pageToken=next_page_token,
        )
        response = request.execute()

        for item in response.get("items", []):
            channel_title = item["snippet"]["title"]
            channel_id = item["id"].get("channelId")
            if channel_id:
                channel_ids.append(channel_id)
                print(f"Channel {len(channel_ids)}: {channel_title}")
                if len(channel_ids) == num_channels:
                    break

        # Check if there's another page of results
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return channel_ids

def subscribe_to_channel(credentials, channel_id):
    youtube = build("youtube", "v3", credentials=credentials)
    try:
        request = youtube.subscriptions().insert(
            part="snippet",
            body={
                "snippet": {
                    "resourceId": {
                        "kind": "youtube#channel",
                        "channelId": channel_id
                    }
                }
            }
        )
        request.execute()
        print(f"Successfully subscribed to channel ID: {channel_id}")
    except HttpError as e:
        error_content = e.content.decode("utf-8")
        if "quotaExceeded" in error_content:
            print("Quota exceeded! Stopping further requests.")
            raise
        else:
            print(f"Failed to subscribe to channel: {error_content}")
### Sub functions for subscribe the channel ends here ### 

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=443, ssl_context=("ssl_certificate/cert.pem", "ssl_certificate/key.pem"), debug=True)


