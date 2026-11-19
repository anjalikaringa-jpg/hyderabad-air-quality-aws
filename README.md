# Hyderabad Air Quality Monitor on AWS

A serverless project that checks Hyderabad's air quality every hour, saves the data, shows it on a simple web page, and sends an email when the air quality level changes.

**Live page:** https://d2gm6fkjuq4y9f.cloudfront.net/

## What it does

- Collects hourly air quality data for Hyderabad (fine dust PM2.5, coarse dust PM10 and the US AQI score) from the free Open-Meteo API.
- Shows the result in plain words (Good, Moderate, Unhealthy) with a short tip, instead of only numbers.
- Lets you pick any day from the last 30 days, or the next 6 days of forecast, and see the best and worst times to be outside.
- Emails me when the air quality level changes, for example from Moderate to Unhealthy for sensitive people.

## How it works

```
EventBridge Scheduler (every hour)
        |
        v
AWS Lambda (Python) ---> Open-Meteo API
        |
        v
Amazon S3 (private bucket: data.json, state.json)
        |                         |
        v                         v
Amazon CloudFront ---> Web page   Amazon SNS ---> Email alert
```

| Service | Role in the project |
|---|---|
| EventBridge Scheduler | Starts the Lambda function every hour |
| Lambda (Python 3.13) | Fetches the data, saves it, checks if the level changed |
| S3 (private) | Stores the data files and the web page |
| CloudFront | Gives the page a public link; the bucket stays private (Origin Access Control) |
| SNS | Sends the email alert |
| IAM | Gives the function access to one bucket and one topic only (least privilege) |
| CloudWatch Logs | Records every run |

## Files

- `README.md` - project overview and architecture guide
- `lambda_function.py` - the code that runs on AWS Lambda
- `index.html` - the web page (reads `data.json`)
- `requirements.txt` - Python dependencies for the project



## What I learned

- Setting up an IAM role with permission for only one bucket and one SNS topic.
- Why a Lambda function needs a longer timeout than the default when it calls a web API.
- Keeping an S3 bucket private and serving it through CloudFront with Origin Access Control.
- Scheduling a function with EventBridge and checking runs in CloudWatch Logs.
- Turning raw numbers into plain-language results that anyone can read.

## Notes

- Data source: [Open-Meteo Air Quality API](https://open-meteo.com/) (free, no key needed). Forecast values are predictions, not measurements.
- This is a learning project, not an official air quality service.
