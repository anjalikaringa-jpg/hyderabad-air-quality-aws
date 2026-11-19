import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta
import boto3

BUCKET = "anjali-hyd-air-quality-2026"
TOPIC_ARN = os.environ.get("TOPIC_ARN", "")
URL = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
    "?latitude=17.385&longitude=78.4867"
    "&hourly=pm2_5,pm10,us_aqi"
    "&past_days=30&forecast_days=7"
    "&timezone=Asia%2FKolkata"
)
LEVELS = [
    (50, "Good", "Fresh air. Enjoy the outdoors."),
    (100, "Moderate", "Fine for most people. Sensitive people should take care."),
    (150, "Unhealthy for sensitive people",
     "Children, older people and anyone with asthma should limit time outside."),
    (10**9, "Unhealthy", "Everyone should cut down on outdoor activity."),
]

s3 = boto3.client("s3")
sns = boto3.client("sns")


def level_of(aqi):
    for limit, name, tip in LEVELS:
        if aqi <= limit:
            return name, tip


def lambda_handler(event, context):
    # 1. Fetch Hyderabad air quality (30 past days + 7 forecast days)
    with urllib.request.urlopen(URL, timeout=20) as response:
        hourly = json.loads(response.read())["hourly"]

    rows = []
    for t, p25, p10, aqi in zip(
        hourly["time"], hourly["pm2_5"], hourly["pm10"], hourly["us_aqi"]
    ):
        if aqi is not None and p25 is not None and p10 is not None:
            rows.append({"time": t, "pm25": p25, "pm10": p10, "aqi": aqi})

    # 2. Save the data for the web page to read
    s3.put_object(
        Bucket=BUCKET, Key="data.json", Body=json.dumps(rows),
        ContentType="application/json", CacheControl="max-age=300",
    )

    # 3. Work out the current air quality level (India time)
    now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%dT%H")
    latest = [r for r in rows if r["time"][:13] <= now][-1]
    name, tip = level_of(latest["aqi"])

    # 4. Compare with the last saved level
    try:
        previous = json.loads(
            s3.get_object(Bucket=BUCKET, Key="state.json")["Body"].read()
        )["level"]
    except Exception:
        previous = None
    s3.put_object(
        Bucket=BUCKET, Key="state.json",
        Body=json.dumps({"level": name}), ContentType="application/json",
    )

    # 5. Send an email notification only when the level changes
    force = isinstance(event, dict) and event.get("force") is True
    changed = previous is not None and previous != name
    if TOPIC_ARN and (changed or force):
        start = "Test alert. " if force and not changed else ""
        move = f"changed from {previous} to {name}" if changed else f"is {name}"
        message = (
            f"{start}Hyderabad air {move}.\n{tip}\n"
            f"(Air score {latest['aqi']}, fine dust PM2.5 {latest['pm25']})"
        )
        sns.publish(TopicArn=TOPIC_ARN, Subject="Hyderabad air quality update", Message=message)

    return {
        "saved_rows": len(rows),
        "level": name,
        "alert_sent": bool(TOPIC_ARN and (changed or force)),
    }
