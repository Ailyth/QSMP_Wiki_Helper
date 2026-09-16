Friendly (more or less) program which fetches when content creator was on server and creates history template, based on info provided in these spreadsheets.
Since we register server day, date, content creator and vod, we are able to make our life easier and fill these templates automatically.
Initially, the plan was to update "abandoned ccs" easily without spending 446578 hours collecting data.

HOWEVER, in order this solution to fully work, a workspace in Google Cloud had to be created, since we cannot just make random API calls to Google resources without authentication, meaning there has to be a mark who viewed a spreadsheet.

I suppose I could just add people to the workspace which I have already created, so authentication would happen only once (per day? month?), generally to be researched but doesn't seem to be a big deal. We could create service account after all, for now it's just a small project, which will be useful (at least) for me.
