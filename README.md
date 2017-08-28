# Ingestor for Contest Result Files

## What are in this folder?
`ingestor_precinct.py` is a simple web app that downloads a precinct result file
and ingest it into the database. It is now running at http://152.2.32.233:5006/ingestor_precinct.

`ingestor_county.py` is a simple web app that downloads a county result file or a county contest file
and ingest it into the database. It is now running at http://152.2.32.233:5006/ingestor_precinct.

## Database Structure

### Precinct Results
Table: contest_precinct

Columns:

Contest related attributes
* election_date
* contest_group_id: an identifier to link a contest across multiple counties
* contest_name
* contest_type: state or county
* party_contest: party of the contest if it is partisan
* is_partisan: whether the election is partisan or not
* vote_for
* term

County related attributes
* district
* county

Precinct related attributes
* precinct

Candidate related attributes
* candidate
* first_name
* middle_name
* last_name
* name_suffix_lbl
* nick_name
* party_candidate: party affiliation of a candidate
* candidacy_date
* is_unexpired: ???
* has_primary: ???
* election_day: number of votes received at the election day
* one_stop: number of one-stop votes
* absentee_by_mail: number of absentee-by-mail votes
* provisional: number of provisional votes
* total_votes: total number of votes
* winner_flag: whether winner of the contest

### County Results
Table: contest_county

Columns: same as contest_precint without precinct
