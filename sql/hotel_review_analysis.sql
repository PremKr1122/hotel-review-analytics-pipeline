show databases;
use hotel_reviews;

show tables;
-- hotels ; review_aspects ; reviews 

select * from reviews limit 10;

-- Total reviews
select count(*) from reviews; -- 254569

-- total rows with null review texts    
select count(*) from reviews 
where review_text is null; -- 25786

select count(*) from reviews where title like '?%'; -- 1682

select count(*) from reviews where title like '?%' and review_text is null; -- 1680

select * from reviews where title not like '?%' and review_text is null limit 20;

-- i.e. almost every row in column review_text is null corresponding to column title contains '?%'

-- I am going to find out the names of the hotel where 'title' like '?%' so it is easy to detect
-- in code that is it a encoding issue or not

-- TOTAL NUMBER OF ROWS CONTAINS '?%' IN TITLE COLUMNS CORRES. TO EACH HOTEL DISTINCTLY 

select count(*) as question_mark_titles, h.hotel_name
from hotels as h
join reviews as r on h.hotel_id = r.hotel_id
where r.title like '?%' group by(h.hotel_name)
order by question_mark_titles desc; 
-- verified using dataset that it is not encoding problem but pre-exist in raw data
-- 1682 titles start with '?', 1680 of them have null review_text

-- lets check out that why rest rows in column review_text is null 
select * 
from reviews 
where title not like '?%' and review_text is null limit 10;

select count(*) 
from reviews 
where title not like '?%' and review_text is null; -- 24105

-- 1680 + 24105 = 25785, one short of 25786. checking rows with null title
select count(*) 
from reviews 
where title is null and review_text is null; -- should be 1

select h.city, count(*)
from reviews as r
join hotels as h on h.hotel_id = r.hotel_id 
where r.title not like '?%' 
and r.review_text is null 
group by(h.city);

select h.hotel_name, count(*) as title_only_reviews
from reviews as r
join hotels as h on h.hotel_id = r.hotel_id 
where r.title not like '?%' and r.review_text is null 
group by(h.hotel_name) order by title_only_reviews desc;

select h.hotel_name, h.city, r.review_date 
from reviews as r
join hotels as h on h.hotel_id = r.hotel_id 
where r.title not like '?%' 
and r.review_text is null; -- verified from dataset : empty text => not encoding prob again

-- Final decision : filter the null rows at query or measure level since it neither contains any 
-- text and nor it is a encoding problem

-- ==> Review Summary...........................  
    
-- Avg sentiment score
select round(avg(sentiment_score),2) from reviews;

-- Weakest aspect
select aspect 
from review_aspects group by(aspect) 
order by avg(aspect_sentiment) 
limit 1;
    
select distinct sentiment_label from reviews;

-- % of positive reviews
select
    round(sum(sentiment_label = 'positive') / count(sentiment_label) * 100, 2) as positive_reviews_pct
from reviews;

-- % of negative reviews 

select
    round(sum(sentiment_label = 'negative') / count(sentiment_label) * 100, 2) as negative_reviews_pct
from reviews;

-- % of neutral reviews

select
    round(sum(sentiment_label = 'neutral') / count(sentiment_label) * 100, 2) as neutral_reviews_pct
from reviews;

-- Reviews tags by frequency 

select
    aspect,
    count(*) as total_mentions,
    round(sum(aspect_sentiment >= 0.05)  / count(*) * 100, 2) as positive_pct,
    round(sum(aspect_sentiment <= -0.05) / count(*) * 100, 2) as negative_pct,
    round(sum(aspect_sentiment > -0.05 and aspect_sentiment < 0.05) / count(*) * 100, 2) as neutral_pct
from review_aspects
group by aspect
order by negative_pct desc;

-- Reviews tag by city (remaining)
select distinct sentiment_label from reviews; -- null is present 

select h.city, count(r.sentiment_label) as reviews_with_text
from hotels as h
join reviews as r on h.hotel_id = r.hotel_id
group by h.city
order by reviews_with_text desc;
    
select h.city as city,
    sum(r.sentiment_label = 'positive') as `Positive`,
    sum(r.sentiment_label = 'negative') as `Negative`,
    sum(r.sentiment_label = 'neutral') as `Neutral`,
    count(*) as Total
from hotels as h
inner join reviews as r on h.hotel_id = r.hotel_id
where r.sentiment_label is not null
group by h.city;



-- Reviews over time 
select distinct year(review_date) as Review_Year from reviews order by Review_Year;

select count(*) from reviews where review_date is not null;
select count(*) from reviews where review_date is null; -- 1587

-- city and hotels with null rows in review_date column 

select 
h.hotel_name, h.city, count(*) as no_date 
from hotels as h
join reviews as r on h.hotel_id = r.hotel_id
where review_date is null
group by h.hotel_name, h.city
order by no_date desc;

-- Confirms whether actually there is no date in raw dataset -- Confirmed it is valid 

-- Total reviews year wise 
select year(review_date) as Yr, count(review_id) as Total 
	from reviews where review_date is not null group by (Yr) order by Yr;
    
    
-- Total reviews month wise 
select monthname(review_date) as Mnth, count(*) as Total
	from reviews where review_date is not null group by month(review_date), monthname(review_date)
    order by month(review_date);

-- review for each year based on all months
select
    monthname(review_date) as month_name,
    sum(year(review_date) = 2001) as `2001`,
    sum(year(review_date) = 2002) as `2002`,
    sum(year(review_date) = 2003) as `2003`,
    sum(year(review_date) = 2004) as `2004`,
    sum(year(review_date) = 2005) as `2005`,
    sum(year(review_date) = 2006) as `2006`,
    sum(year(review_date) = 2007) as `2007`,
    sum(year(review_date) = 2008) as `2008`,
    sum(year(review_date) = 2009) as `2009`,
    count(*) as total
from reviews
where review_date is not null
group by month(review_date), monthname(review_date)
order by month(review_date);
-- ======================================================

-- Complaints Details .................

select
    count(sentiment_label) as reviews_with_text,
    sum(sentiment_label = 'negative') as complaints,
    round(sum(sentiment_label = 'negative') / count(sentiment_label) * 100, 2) as complaint_pct
from reviews;

select
    aspect,
    count(*) as mentions,
    sum(aspect_sentiment <= -0.05) as complaints,
    round(sum(aspect_sentiment <= -0.05) / count(*) * 100, 2) as complaint_pct
from review_aspects
group by aspect
order by complaint_pct desc;

select
    h.city,
    count(r.sentiment_label) as reviews_with_text,
    sum(r.sentiment_label = 'negative') as complaints,
    round(sum(r.sentiment_label = 'negative') / count(r.sentiment_label) * 100, 2) as complaint_pct
from reviews as r
join hotels as h on h.hotel_id = r.hotel_id
group by h.city
order by complaint_pct desc;

select
    h.hotel_name,
    h.city,
    count(r.sentiment_label) as reviews_with_text,
    sum(r.sentiment_label = 'negative') as complaints,
    round(sum(r.sentiment_label = 'negative') / count(r.sentiment_label) * 100, 2) as complaint_pct
from reviews as r
join hotels as h on h.hotel_id = r.hotel_id
group by h.hotel_id, h.hotel_name, h.city
having count(r.sentiment_label) >= 50
order by complaint_pct desc
limit 20;

select
    h.hotel_name,
    h.city,
    r.review_date,
    ra.aspect_sentiment,
    left(r.review_text, 200) as snippet
from review_aspects as ra
join reviews as r on r.review_id = ra.review_id
join hotels as h on h.hotel_id = r.hotel_id
where ra.aspect = 'noise'
  and ra.aspect_sentiment <= -0.05
order by ra.aspect_sentiment
limit 20;

select
    h.city,
    ra.aspect,
    count(*) as complaints
from review_aspects as ra
join reviews as r on r.review_id = ra.review_id
join hotels as h on h.hotel_id = r.hotel_id
where ra.aspect_sentiment <= -0.05
group by h.city, ra.aspect
order by h.city, complaints desc;

select
    year(review_date) as review_year,
    count(sentiment_label) as reviews_with_text,
    sum(sentiment_label = 'negative') as complaints,
    round(sum(sentiment_label = 'negative') / count(sentiment_label) * 100, 2) as complaint_pct
from reviews
where review_date is not null
group by year(review_date)
order by review_year;

select
    review_id,
    count(*) as complaint_aspects,
    group_concat(aspect order by aspect) as aspects
from review_aspects
where aspect_sentiment <= -0.05
group by review_id
having count(*) >= 3
order by complaint_aspects desc
limit 20;