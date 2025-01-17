from flask import Flask, render_template, request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

@app.route('/')
def index():
    return render_template('submit.html')

@app.route('/submit', methods=['POST'])
def submit():
    query = request.form['query']
    num_videos = 1
    # num_videos = int(request.form['num_videos'])

    creds = authenticate()
    video_ids = search_youtube(creds, query, num_videos)
    # search for multiple keywords
    # video_ids = search_youtube(creds, query, num_videos)

    if video_ids:
        for video_id in video_ids:
            try:
                like_video(creds, video_id)
            except HttpError as e:
                if "quotaExceeded" in str(e):
                    return "Quota exceeded! Try again tomorrow."
    
    return f"Search for '{query}' with {num_videos} videos completed, and all found videos have been liked!"


def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret_from20250115_desktop_sub.json", SCOPES
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


