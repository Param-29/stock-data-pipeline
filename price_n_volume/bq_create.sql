CREATE OR REPLACE EXTERNAL TABLE `quick-ray-375906.price_n_volume.recent_raw_external`
  OPTIONS (
    format ="csv",
    uris = ['gs://prefect-dee/data/price_n_volume/recent/*']
    );

CREATE or REPLACE TABLE `quick-ray-375906.price_n_volume.recent_raw`
AS 
SELECT * FROM `quick-ray-375906.price_n_volume.recent_raw_external`;
