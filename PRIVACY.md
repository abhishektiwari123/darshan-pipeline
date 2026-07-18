# Privacy Policy — Darshan Pipeline

**Effective date:** 18 July 2026
**Contact:** abhishektiwari29867@gmail.com

Darshan Pipeline ("the tool") is a private command-line application used by its operator to manage live broadcasts on YouTube channels the operator owns. This policy describes what data the tool accesses and how it is handled.

## What the tool accesses

The tool uses YouTube API Services (YouTube Data API v3) after the operator grants OAuth 2.0 consent. With that consent it accesses, **only for channels the operator owns**:

- Channel identity (channel name/ID) — to confirm which channel a token controls
- Live broadcast and live stream resources (titles, schedule, status, ingestion keys) — to create, update, bind, and delete the operator's own broadcasts

The tool does **not** access, collect, or process data belonging to any other person or channel. It does not read comments, subscriber lists, analytics, or any viewer data.

## How data is stored

- OAuth tokens are stored **locally on the operator's own computer** in files readable only by the operator's user account. No database and no server are involved.
- The tool retains no other YouTube data; API responses are used transiently to execute the requested command and are not persisted.

## What is shared

Nothing. Data is exchanged only between the tool (running on the operator's machine) and Google's YouTube API endpoints over HTTPS. No third parties receive any data. The tool serves no ads and has no analytics.

## Google API Services compliance

The tool's use of information received from Google APIs adheres to the [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy), including the Limited Use requirements, and to the [YouTube API Services Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service). Users can revoke the tool's access at any time via [Google security settings](https://myaccount.google.com/permissions), and data can be deleted by removing the local token files.

## Changes

Any changes to this policy will be published on this page.
