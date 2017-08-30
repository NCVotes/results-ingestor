# Ingestor for Contest Result Files

## What are in this folder?
`ingestor_precinct.py` is a simple web app that downloads a precinct result file
and ingest it into the database. It is now running at http://152.2.32.233:5006/ingestor_precinct.

`ingestor_county.py` is a simple web app that downloads a county result file or a county contest file
and ingest it into the database. It is now running at http://152.2.32.233:5006/ingestor_county.

They are written bokeh in python, and can be run as `bokeh serve ingestor_precinct.py ingestor_county.py --allow-websocket-origin=*`

## Database Structure

### Precinct Results
Table: contest_precinct

Columns:

Contest related attributes
* election_date
* contest_group_id: an identifier to link a contest across multiple counties
* contest_name
* contest_type: state or county
* is_partisan: whether the election is partisan or not
* has_primary: whether a candidate for a particular contest first must compete in a primary before running in a general election. For partisan races, this value will be true if the number of candidates in a particular party in a particular a contest is greater than the value in the vote_for field (the number of seats that are up for election). If candidates > seats for a given party, then the board of elections will actually hold a primary, print ballots, etc. If candidates <= seats for a given party, then the board of elections will not bother with holding a primary, etc., since the result is a foregone conclusion. For non-partisan races (some of which still have primaries) this value will be true only if the number of candidates in any party exceeds the number of seats up for grabs. As this field exists in the candidate listing CSV found in #7, the value of TRUE only indicates the relationship between the number of candidates and the open seats. At least in this CSV, the field is not an indicator of whether rules for a contest require a primary. For example, if there is only one Republican candidate in a single-seat contest for which rules require a partisan primary then the value of has_primary would be FALSE. 
* party_contest: is null unless both has_primary and is_partisan are TRUE. The values of party_contest should be DEM, REP or LIB.
* vote_for
* term
* is_unexpired: whether an contest is being held before the normal expiration of the previous incumbent's term. 

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
* election_day: number of votes received at the election day
* one_stop: number of one-stop votes
* absentee_by_mail: number of absentee-by-mail votes
* provisional: number of provisional votes
* total_votes: total number of votes
* winner_flag: whether winner of the contest

### County Results
Table: contest_county

Columns: same as contest_precinct without precinct

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
    sum(total_votes) as total_votes,
    sum(winner_flag) as winner_flag
FROM contest_precinct
GROUP BY election_date, contest_group_id, contest_name, district, county, candidate;
```




