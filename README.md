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

Columns: same as contest_precinct without precinct

It is aggreated from precinct results by the following code



The county-level result table is aggregated from the precinct result table with the following code
```
CREATE TABLE contest_county
AS
SELECT election_date, 
	contest_group_id, 
    contest_name, 
    string_agg(distinct contest_type,'|') as contest_type, 
    string_agg(distinct party_contest,'|') as party_contest, 
    district, 
    county, 
    max(vote_for) as vote_for, 
    candidate, 
    string_agg(distinct first_name,'|') as first_name, 
    string_agg(distinct middle_name,'|') as middle_name, 
    string_agg(distinct last_name,'|') as last_name, 
    string_agg(distinct name_suffix_lbl,'|') as name_suffix_lbl, 
    string_agg(distinct nick_name,'|') as nick_name, 
    max(candidacy_date) as candidacy_date, 
    string_agg(distinct party_candidate,'|') as party_candidate, 
    bool_or(is_unexpired) as is_unexpired, 
    bool_or(has_primary) as has_primary, 
    bool_or(is_partisan) as is_partisan, 
    string_agg(distinct term,'|') as term, 
    sum(absentee_by_mail) as absentee_by_mail, 
    sum(one_stop) as one_stop, 
    sum(provisional) as provisional, 
    sum(election_day) as election_day, 
    sum(total_votes) as total_votes
FROM contest_precinct
GROUP BY election_date, contest_group_id, contest_name, district, county, candidate;
```




