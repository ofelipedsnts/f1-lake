# %%
import nekt
import os
import dotenv

# %%
dotenv.load_dotenv()

NEKT_TOKEN = os.getenv("NEKT_TOKEN")
nekt.data_access_token = NEKT_TOKEN
# %%


# Query importada do explorer
query = """
SELECT 
  date('{date}') AS date_ref,

  driverid,

  count(*) AS total_sessions,

  sum(
    CASE WHEN mode = 'Race' THEN 1 ELSE 0 END
  ) AS total_races,

  sum(
    CASE WHEN mode = 'Sprint' THEN 1 ELSE 0 END
  ) AS total_sprints,

  sum(
    CASE
      WHEN status = 'Finished' AND mode = 'Race' THEN 1 ELSE 0 END
  ) AS finished_races,

  sum(
    CASE
      WHEN status = 'Finished' AND mode = 'Sprint' THEN 1 ELSE 0 END
  ) AS finished_sprints,

  sum(
    CASE WHEN position = 1 THEN 1 ELSE 0 END
  ) AS total_victories,

  sum(
    CASE WHEN position = 1 AND mode = 'Race' THEN 1 ELSE 0 END
  ) AS race_victories_count,

  sum(
    CASE WHEN position = 1 AND mode = 'Sprint' THEN 1 ELSE 0 END
  ) AS sprint_victories_count,


  sum(points) AS total_points,

  sum(
    CASE WHEN mode = 'Race' THEN points END
  ) AS total_race_points,

  sum(
    CASE WHEN mode = 'Sprint' THEN points END
  ) AS total_sprint_points,

  sum(
    CASE
      WHEN points >= 1 AND mode = 'Race' THEN 1 ELSE 0 END
  ) AS races_with_points,

  sum(
    CASE
      WHEN points >= 1 AND mode = 'Sprint' THEN 1 ELSE 0 END
  ) AS sprints_with_points,

  sum(
    CASE
      WHEN position <= 3 THEN 1 ELSE 0 END
  ) AS total_podiums,

  sum(
    CASE
      WHEN position <= 3 AND mode = 'Sprint' THEN 1 ELSE 0 END
  ) AS total_sprint_podiums,

  sum(
    CASE
      WHEN position <= 3 AND mode = 'Race' THEN 1 ELSE 0 END
  ) AS total_race_podiums,

  sum(
    CASE 
      WHEN gridposition <= 3 THEN 1 ELSE 0 END
  ) AS pole_positions_count,

  sum(
    CASE 
      WHEN gridposition = 1 AND mode = 'Race'THEN 1
      WHEN gridposition = 2 AND mode = 'Race' THEN 1
      WHEN gridposition = 3 AND mode = 'Race' THEN 1
      ELSE 0 END 
  ) AS race_pole_positions_count,

  sum(
    CASE 
      WHEN gridposition = 1 AND mode = 'Sprint'THEN 1
      WHEN gridposition = 2 AND mode = 'Sprint' THEN 1
      WHEN gridposition = 3 AND mode = 'Sprint' THEN 1
      ELSE 0 END 
  ) AS sprint_pole_positions_count,

  sum(
    CASE WHEN gridposition = 1 THEN 1 ELSE 0 END
  ) AS total_sessions_started_first,

  sum(
    CASE WHEN gridposition = 1 AND mode = 'Race' THEN 1 ELSE 0 END
  ) AS total_races_started_first,

  sum(
    CASE WHEN gridposition = 1 AND mode = 'Sprint' THEN 1 ELSE 0 END
  ) AS total_sprint_started_first,

  sum(
    CASE WHEN gridposition <= 5 AND mode = 'Race' THEN 1 ELSE 0 END
  ) AS race_top_5_classification_count,

  sum(
    CASE WHEN gridposition <= 5 AND mode = 'Sprint' THEN 1 ELSE 0 END
  ) AS sprint_top_5_classification_count,

  round(avg(gridposition),0) AS avg_gridposition,

  round(avg(
    CASE WHEN mode = 'Race' THEN gridposition END
  ),0) AS avg_race_gridposition,

  round(avg(
    CASE WHEN mode = 'Sprint' THEN gridposition END
  ),0) AS avg_sprint_gridposition,

  round(avg(position),0) AS avg_finished_position,

  round(avg(
    CASE WHEN mode = 'Race' THEN position END
  ),0) AS avg_race_finished_position,

  round(avg(
    CASE WHEN mode = 'Sprint' THEN position END
  ),0) AS avg_sprint_finished_position,

  sum(
    CASE WHEN position = 1 AND gridposition = 1 THEN 1 ELSE 0 END
  ) AS started_and_finished_first,

  sum(
    CASE WHEN gridposition <= 3 AND position = 1 THEN 1 ELSE 0 END
  ) AS started_poleposition_and_finished_first,

  sum(
    CASE WHEN position > gridposition THEN 1 ELSE 0 END
  ) AS finished_position_negative,

  sum(
    CASE WHEN position > gridposition AND MODE = 'Race' THEN 1 ELSE 0 END
  ) AS race_finished_position_negative,

  sum(
    CASE WHEN position > gridposition AND MODE = 'Sprint' THEN 1 ELSE 0 END
  ) AS sprint_finished_position_negative,

  sum(
    CASE WHEN position < gridposition THEN 1 ELSE 0 END
  ) AS sessions_with_overtake,

  sum(
    CASE WHEN position < gridposition AND mode = 'Race' THEN 1 ELSE 0 END
  ) AS races_with_overtake,

  sum(
    CASE WHEN position < gridposition AND mode = 'Sprint' THEN 1 ELSE 0 END
  ) AS sprints_with_overtake,

  round(avg(gridposition - position),2) AS avg_overtakes,

  round(avg(
    CASE WHEN mode = 'Race' THEN gridposition - position END
  ),2) AS avg_race_overtakes,

  round(avg(
    CASE WHEN mode = 'Sprint' THEN gridposition - position END
  ),2) AS avg_sprint_overtakes,

  count(DISTINCT year) as seasons_count

FROM driver_results
GROUP BY driverid
ORDER BY driverid
"""

date_query = """
SELECT DISTINCT date(date) AS dt_ref FROM f1_results
ORDER BY dt_ref
"""

# Carregamento das tabelas necessárias
(
    nekt.load_table(
        layer_name="bronze",
        table_name="driver_results"
    ).createOrReplaceTempView("driver_results")
)

(
    nekt.load_table(
        layer_name="bronze",
        table_name="f1_results"
    ).createOrReplaceTempView("f1_results")
)

# Iniciar spark session
spark = nekt.get_spark_session()

dates = spark.sql(date_query).toPandas()["dt_ref"].tolist()[:10]

df_all = spark.sql(query.format(date=dates.pop(0)))

for dt in dates:
    df_all = df_all.union(
        spark.sql(query.format(date=dt))
    )

# DF resultante da query
df = spark.sql(query)

nekt.save_table(
    df=df,
    layer_name="silver",
    table_name="fs_driver_results_life",
    folder_name="f1"
)
# %%
