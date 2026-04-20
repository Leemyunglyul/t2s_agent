### City legislation

#### City legislation 질문 정리

##### Instance Id: local068

Calculate the number of new cities inserted in April, May, and June for each year from 2021 to 2023. For each month, compute the cumulative running total of cities added for that specific month across the years up to and including the given year (i.e., sum the counts of that month over the years). Additionally, calculate the year-over-year growth percentages for both the monthly total and the running total for each month, comparing each year to the previous year. Present the results only for 2022 and 2023, listing the year, the month, the total number of cities added in that month, the cumulative running total for that month, and the year-over-year growth percentages for both the monthly total and the running total. Use the data from 2021 solely as a baseline for calculating growth rates, and exclude it from the final output.

대상: 데이터베이스에 등록된 신규 도시 데이터

기간: 2021년 ~ 2023년 (3개년), 매년 4월, 5월, 6월 데이터만 대상

목표:

1. 월별 집계: 각 연도/월별로 추가된 도시의 총 개수 계산.

2. 누적합(Running Total) 계산: 특정 월(예: 4월)에 대해 2021년부터 해당 연도까지의 누적 합계를 계산.

3. 성장률(YoY) 계산: 전년 동월 대비 '월별 총계' 및 '누적 합계'의 성장 퍼센트(%) 계산.

데이터 선택 (최종 출력): 연도(Year), 월(Month), 월별 도시 추가 수, 누적 합계, 월별 성장률(%), 누적합 성장률(%) 리스트업.

특이사항: 2021년 데이터는 성장률 계산을 위한 기준점(Baseline)으로만 사용하며, 최종 결과물에서는 제외함. 즉, 결과창에는 2022년과 2023년 데이터만 표시되어야 함.

##### Instance Id: local070

Please examine our database records for Chinese cities (country_code_2 = 'cn') during July 2021 and identify both the shortest and longest streaks of consecutive date entries. For each date in these streaks, return exactly one record per date along with the corresponding city name. In your output, please ensure the first letter of each city name is capitalized and the rest are lowercase. Display the dates and city names for both the shortest and longest consecutive date streaks, ordered by date.

대상: 중국 데이터

기간: 2021년 7월 한 달간의 기록

목표: 연속된 날짜 스트릭(streak) 찾기, 최단/최장 스트릭 식별

데이터 선택: 해당 스트릭에 포함된 날짜별로 정확히 하나의 레코드와 도시 이름을 반환.

이름 변환: 도시 이름의 첫 글자는 대문자, 나머지는 소문자로 표시해야 합니다 (예: beijing → Beijing).

정렬: 최종 결과물은 날짜(Date) 순으로 정렬.

##### Instance Id: local071

Could you review our records in June 2022 and identify which countries have the longest streak of consecutive inserted city dates? Please list the 2-letter length country codes of these countries.

대상: 전 세계 국가 (특정 국가 지정 없음)

기간: 2022년 6월 한 달간의 기록

목표: 도시 데이터가 입력된 날짜 중, 날짜가 끊기지 않고 가장 길게 이어진 최장 스트릭(Longest streak)을 보유한 국가 찾기.

데이터 선택: 해당 조건을 만족하는 국가의 2글자 국가 코드(country_code_2)를 추출.

특이사항: 여러 국가가 공동 1위(최장 스트릭 동일)일 경우 해당 국가들을 모두 리스트업해야 함.

##### Instance Id: local072

Identify the country with data inserted on nine different days in January 2022. Then, find the longest consecutive period with data insertions for this country during January 2022, and calculate the proportion of entries that are from its capital city within this longest consecutive insertion period.

대상: 2022년 1월 데이터 중 특정 조건을 만족하는 국가

조건 1 (대상 국가 식별): 2022년 1월 한 달 동안, 서로 다른 날짜 9일에 걸쳐 데이터가 입력된 국가를 찾기.

조건 2 (최장 스트릭 찾기): 식별된 해당 국가의 1월 기록 중, 날짜가 끊기지 않고 가장 길게 이어진 최장 연속 입력 기간(Longest consecutive period)을 확인.

목표 (최종 계산): 위에서 찾은 '최장 연속 입력 기간' 내에 발생한 전체 데이터 중, 해당 국가의 수도(Capital city)에서 입력된 데이터가 차지하는 비율(Proportion)을 계산.

##### Instance Id: local167

Based on the state each female legislator first represented, which state has the highest number of female legislators whose terms included December 31st at any point, and what is that count? Please provide the state's abbreviation.

대상: 여성 의원 (Female legislators)

조건 1 (날짜 기준): 임기 기간 중 어느 시점이든 '12월 31일'이 포함된 적이 있는 의원들만 선별.

조건 2 (기준 주 식별): 각 의원이 '생애 처음으로(first represented)' 소속되었던 주(State)를 기준으로 집계. (한 의원이 여러 주에서 활동했을 가능성 고려)

목표: 위 조건을 만족하는 여성 의원 수가 가장 많은 주를 찾고, 그 의원 수(Count)를 계산.

데이터 선택 (최종 출력): 해당 주의 약어(Abbreviation)와 의원 수를 반환.

##### Instance Id: local168

Among job postings that specifically have the Data Analyst, require a non-null annual average salary, and are remote, what is the overall average salary when considering only the top three most frequently demanded skills for these positions?

대상: 구인 공고 (Job Postings)

조건 1 (직무 및 형태): 직무 타이틀이 **'Data Analyst'**여야 하며, 원격 근무(Remote) 포지션만 대상.

조건 2 (데이터 품질): 연봉 정보(annual average salary)가 비어있지 않은(non-null) 레코드만 포함.

조건 3 (기술 스택 필터): 위 조건에 부합하는 전체 공고 중에서 가장 많이 요구된 **상위 3개의 기술(Skills)**을 식별.

목표 (최종 계산): 식별된 상위 3개 기술 중 최소 하나를 요구하는 공고들의 전체 평균 연봉을 계산.

###### Gold SQL

```sql
WITH FilteredJobPostings AS (
    SELECT
        job_id,
        salary_year_avg
    FROM
        job_postings_fact
    WHERE
        job_title_short = 'Data Analyst'
        AND salary_year_avg IS NOT NULL
        AND job_work_from_home = 1
),
SkillCounts AS (
    SELECT
        sjd.skill_id,
        sd.skills AS skill_name,
        COUNT(DISTINCT fjp.job_id) AS job_count
    FROM
        FilteredJobPostings AS fjp
    JOIN
        skills_job_dim AS sjd ON fjp.job_id = sjd.job_id
    JOIN
        skills_dim AS sd ON sjd.skill_id = sd.skill_id
    GROUP BY
        sjd.skill_id,
        sd.skills
),
Top3Skills AS (
    SELECT
        skill_id
    FROM
        (
            SELECT
                skill_id,
                DENSE_RANK() OVER (ORDER BY job_count DESC) AS rnk
            FROM
                SkillCounts
        ) AS ranked_skills
    WHERE
        rnk <= 3
)
SELECT
    AVG(fjp.salary_year_avg)
FROM
    FilteredJobPostings AS fjp
WHERE
    fjp.job_id IN (
        SELECT DISTINCT
            sjd.job_id
        FROM
            skills_job_dim AS sjd
        JOIN
            Top3Skills AS t3s ON sjd.skill_id = t3s.skill_id
    );
```

##### Instance Id: local169

What is the annual retention rate of legislators who began their first term between January 1, 1917 and December 31, 1999, measured as the proportion of this cohort still in office on December 31st for each of the first 20 years following their initial term start? The results should show all 20 periods in sequence regardless of whether any legislators were retained in a particular year.

분석 대상 (코호트): 1917년 1월 1일부터 1999년 12월 31일 사이에 **생애 첫 임기(First term)**를 시작한 의원들.

측정 지표 (유지율): 위 코호트에 속한 의원들 중, 첫 임기 시작일로부터 이후 1년~20년이 경과한 시점의 매년 12월 31일에 여전히 재직 중인 의원의 비율.

목표: 각 연차별(1년 차~20년 차) 유지율을 순차적으로 계산.

예: (1년 후 12월 31일 재직자 수 / 전체 코호트 인원)

출력 형식: 1년 차부터 20년 차까지의 데이터를 순서대로 나열.

특이사항: 특정 연도에 재직 중인 의원이 없더라도(비율이 0이더라도) 20개의 기간을 모두 빠짐없이 표시해야 함.

```sql
WITH LegislatorFirstTerm AS (
  SELECT
    id_bioguide,
    MIN(term_start) AS first_term_start
  FROM legislators_terms
  GROUP BY
    id_bioguide
), InitialCohort AS (
  SELECT
    id_bioguide,
    first_term_start
  FROM LegislatorFirstTerm
  WHERE
    first_term_start BETWEEN '1917-01-01' AND '1999-12-31'
), Periods AS (
  SELECT 1 AS period_number UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
  SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL
  SELECT 11 UNION ALL SELECT 12 UNION ALL SELECT 13 UNION ALL SELECT 14 UNION ALL SELECT 15 UNION ALL
  SELECT 16 UNION ALL SELECT 17 UNION ALL SELECT 18 UNION ALL SELECT 19 UNION ALL SELECT 20
), CohortPeriodChecks AS (
  SELECT
    T1.id_bioguide,
    T2.period_number,
    CAST(
      (
        CAST(STRFTIME('%Y', T1.first_term_start) AS INTEGER) + T2.period_number - 1
      ) AS TEXT
    ) || '-12-31' AS check_date
  FROM InitialCohort AS T1
  CROSS JOIN Periods AS T2
), RetainedLegislators AS (
  SELECT DISTINCT
    T1.id_bioguide,
    T1.period_number
  FROM CohortPeriodChecks AS T1
  JOIN legislators_terms AS T2
    ON T1.id_bioguide = T2.id_bioguide
  WHERE
    T1.check_date BETWEEN T2.term_start AND T2.term_end
), YearlyRetentionCounts AS (
  SELECT
    period_number,
    COUNT(id_bioguide) AS number_retained
  FROM RetainedLegislators
  GROUP BY
    period_number
)
SELECT
  T1.period_number AS year_after_start,
  COALESCE(T2.number_retained, 0) AS number_retained,
  CAST(COALESCE(T2.number_retained, 0) AS REAL) / (
    SELECT
      COUNT(*)
    FROM InitialCohort
  ) AS retention_rate
FROM Periods AS T1
LEFT JOIN YearlyRetentionCounts AS T2
  ON T1.period_number = T2.period_number
ORDER BY
  year_after_start;
```

##### Instance Id: local170

Identify the state abbreviations where, for both male and female legislators, the retention rate remains greater than zero at specific intervals of 0, 2, 4, 6, 8, and 10 years after their first term start date. A legislator is considered retained if they are serving on December 31 of the respective year. Only include states where both gender cohorts maintain non-zero retention rates at all six of these time points during the first decade of service.

대상: 남성 및 여성 의원 (Both male and female legislators)

측정 시점: 첫 임기 시작일로부터 0년, 2년, 4년, 6년, 8년, 10년이 경과한 시점 (총 6개 지점).

유지(Retained) 정의: 해당 연도의 12월 31일에 의원직을 수행 중인 경우.

조건: 특정 주(State)에서 남성 코호트와 여성 코호트 모두가 위 6개 시점 전부에 대해 유지율이 0보다 커야 함 (즉, 각 시점마다 남녀 모두 최소 1명 이상은 재직 중이어야 함).

목표: 이 엄격한 조건을 만족하는 주의 **약어(State abbreviations)**를 식별.

##### Instance Id: local171

For male legislators from Louisiana, how many distinct legislators were actively serving on December 31 of each year from more than 30 years since their first term up to less than 50 years, grouping the results by the exact number of years elapsed since their first term?

대상: 루이지애나 주(Louisiana) 출신의 남성 의원.

조건 1 (경력 범위): 생애 첫 임기 시작일로부터 30년 초과 ~ 50년 미만이 경과한 시점의 의원들만 대상.

조건 2 (활동 판별): 해당 경력 연차에 해당하는 매년 12월 31일에 실제로 의직을 수행(Serving) 중이었어야 함.

목표: 첫 임기 시작 후 경과된 **'정확한 연수(Exact number of years elapsed)'**를 기준으로 그룹화하여, 각 연차별로 활동했던 **중복 없는 의원 수(Distinct count)**를 계산.

데이터 선택 (최종 출력): 경과 연수(Years elapsed)와 해당 연수의 의원 수 리스트.

##### Instance Id: local202

For alien data, how many of the top 10 states by alien population have a higher percentage of friendly aliens than hostile aliens, with an average alien age exceeding 200?

대상: 외계인 데이터 (alien_data 및 관련 테이블)

조건 1 (그룹화 및 정렬): 외계인 인구수가 가장 많은 상위 10개 주(State)를 선정.

조건 2 (비율 비교): 선정된 각 주 내에서 우호적인 외계인(friendly)의 비율이 적대적인 외계인(hostile)의 비율보다 높아야 함.

조건 3 (나이 제한): 해당 주의 외계인 평균 나이가 200세를 초과해야 함.

목표: 위 세 가지 조건을 모두 만족하는 주의 개수(Count)를 계산.

#### 시행착오

##### 1차 시도: Spider-agent-lite (1/10)

| Task ID      | 최종 상태   | 소요 단계(Steps) | 결과 요약 및 원인                                                         |
| ------------ | ----------- | ---------------- | ------------------------------------------------------------------------- |
| **local202** | 🟢 성공     | 16               | **유일한 정답 도출.** `cat` 명령어로 스키마를 직접 읽고 완벽한 쿼리 작성. |
| **local167** | 🟡 포기     | 15               | `terms` 테이블을 못 찾고 "데이터가 없어 풀 수 없다"며 자진 종료.          |
| **local171** | 🟡 포기     | 15               | 주(State) 정보를 못 찾고 "데이터 없음"으로 자진 종료.                     |
| **local071** | 🟡 포기     | 19               | `country_code` 컬럼을 못 찾고 "국가 정보 누락"으로 자진 종료.             |
| **local168** | 🔴 타임아웃 | 20 (Max)         | 스키마 안 읽고 `job_postings` 관련 테이블 상상하다 종료.                  |
| **local169** | 🔴 타임아웃 | 20 (Max)         | 재귀(Recursive) CTE 문법 오류 및 CSV 파일을 DB 테이블로 착각.             |
| **local170** | 🔴 타임아웃 | 20 (Max)         | `sessions`, `districts` 등 존재하지 않는 테이블 조인 시도하다 종료.       |
| **local068** | 🔴 타임아웃 | 20 (Max)         | `legislation_types`, `established_date` 등 환각 루프.                     |
| **local070** | 🔴 타임아웃 | 20 (Max)         | `events`, `city_data` 등 환각 루프.                                       |
| **local072** | 🔴 타임아웃 | 20 (Max)         | `country_data`, `legislation_data` 등 환각 루프.                          |

치명적인 실패 원인 분석 (The 3 Bugs)

대부분의 실패(🔴, 🟡)는 에이전트의 SQL 코딩 능력이 부족해서가 아니라, **'도구 사용 방식의 결함'** 때문에 발생했습니다.

**'맹인 비행 (Blind Operation)'의 반복**

가장 큰 문제는 에이전트가 `LOCAL_DB_SQL` 액션으로 데이터베이스 목록(`tables.csv`)이나 스키마(`schema.csv`)를 파일로 **저장만 해두고, 정작 열어보지 않는다**는 점입니다.

- **실패 로그들의 공통점:** 파일을 만들고 나서 `Bash(code="cat tables.csv")` 명령어를 쓰지 않습니다. 대신 프롬프트의 영어 단어(city, legislation, job)를 보고 데이터베이스에 있을 법한 테이블 이름을 **상상해서 쿼리를 날립니다.**

**스키마 환각 및 과적합 (Schema Hallucination)**

데이터베이스의 실제 구조를 보지 않으니 끝없는 환각에 빠집니다.

- "도시(City) 문제니까 당연히 `city_data` 테이블이 있겠지?" ➡️ 에러
- "그럼 `events` 테이블인가?" ➡️ 에러
- "의원(Legislator) 문제니까 `state_legislators` 테이블이 있을 거야!" ➡️ 에러
- 에러를 맞고도 스키마를 확인하려 하지 않고 이름만 바꿔가며 20번의 턴을 모두 낭비합니다.

**CSV 파일을 DB 테이블로 착각 (local169 사례)**

`local169` 로그를 보면 아주 특이한 에러가 있습니다.

- 에이전트가 앞선 과정에서 `legislator_first_term_filtered.csv`라는 중간 결과 파일을 만들었습니다.
- 그런데 다음 쿼리에서 `FROM legislator_first_term_filtered` 라고 **CSV 파일 이름을 마치 SQL 테이블 이름인 것처럼 쿼리에 넣어버립니다.** 환경에 대한 이해도(Context)가 무너진 상황입니다.

유일한 성공 사례 (`local202`)가 주는 교훈

그렇다면 `local202` (외계인 인구 통계 문제)는 어떻게 성공했을까요? 로그를 보면 해답이 명확합니다.

1. **Step 7 & 11 & 13:** 에이전트가 `Bash(code="cat aliens_schema.csv")` 등을 사용하여 **자신이 뽑아낸 스키마 파일을 직접 눈으로 읽었습니다!**
2. 실제 컬럼명(`aggressive`, `age`, `state`)을 정확히 인지했습니다.
3. 이를 바탕으로 `WITH` 구문(CTE)과 윈도우 함수를 결합한 엄청나게 복잡한 정답 쿼리를 단 한 번의 에러 없이 완벽하게 짜냈습니다.

**즉, 에이전트의 'SQL 실력'은 이미 최상급입니다. 눈만 뜨게(cat 명령어 사용) 해주면 모든 문제를 풀 수 있습니다.**

Spider-Agent-Lite 환경에서 10개의 과제를 테스트한 결과, 모델의 SQL 작성 능력 자체는 우수하나 **'자율적 환경 탐색 기법'에 치명적인 결함**이 있음을 확인했다. 에이전트는 DB 스키마를 CSV로 추출한 뒤 이를 명시적으로 조회(`cat` 명령어)하지 않고, 사전 학습된 지식에 의존해 테이블과 컬럼명을 환각(Hallucinate)하는 '맹인 비행' 패턴을 보였다.

> 유일하게 성공한 `local202` 케이스는 에이전트가 우연히 `cat` 명령어를 활용하여 실제 스키마를 인지한 경우였다. 따라서 LLM 에이전트의 신뢰성을 높이기 위해서는 **'파일 생성 직후 반드시 파일 읽기 도구를 사용하도록 강제하는 프롬프트 엔지니어링(System Prompting)'**이 필수적으로 수반되어야 한다.

**[실제 코드 해결책]**
계속해서 테스트를 성공시키고 싶으시다면, `spider-agent-lite` 코드 내부의 `system_message` 맨 아래에 이 한 줄을 강제로 추가해 보세요.

> _"CRITICAL RULE: Whenever you output data to a .csv file (like tables.csv or schema.csv), your VERY NEXT action MUST be `Bash(code="cat <filename>")` to read it. NEVER guess table or column names."_

##### 2차 시도: 파일 읽기 도구 사용 강제하는 프롬프트 추가 (2/10)

전체 로그를 분석해 본 결과, 에이전트의 행동 패턴이 180도 달라졌습니다. 이전 실험에서 가장 큰 문제였던 **'맹인 비행(Blind Operation)'과 '스키마 환각(Hallucination)' 현상이 100% 완벽하게 근절**되었습니다.

| Task ID      | 최종 상태    | 소요 단계 | 결과 요약 및 변화                                                                                                                                                                    |
| ------------ | ------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **local068** | 🟢 **성공**  | 12        | **[드라마틱한 변화]** 이전엔 환각으로 20턴을 날렸으나, 이번엔 스키마를 제대로 읽고 12턴 만에 복잡한 누적합/성장률 쿼리를 완벽히 작성해 정답 도출!                                    |
| **local202** | 🟢 **성공**  | 16        | 이전과 마찬가지로 스키마를 꼼꼼히 읽고 정답 완벽 도출.                                                                                                                               |
| **local072** | 🟡 정상종료  | 18        | 실제 데이터를 직접 열어본 후, "2023년 데이터만 있고 문제에서 요구한 2022년 데이터가 없다"는 **팩트를 정확히 파악**하고 합리적으로 작업을 종료함. (환각 없음)                         |
| **local070** | 🔴 타임아웃  | 20        | **[환각 사라짐]** 스키마는 잘 읽었으나, 데이터를 파싱하는 로직을 고민하다 턴 수 부족.                                                                                                |
| **local071** | 🔴 타임아웃  | 20        | **[환각 사라짐]** 스키마를 정확히 확인 후, SQL로 풀기 어렵다 판단하여 **파이썬 스크립트(`calculate_streaks.py`)를 직접 작성해 실행**하는 고도의 추론을 보였으나 턴 수 부족으로 종료. |
| **local168** | 🔴 타임아웃  | 20        | 스키마는 정상 확인했으나, 복잡한 다중 조인(Join) 로직을 짜다가 턴 수 부족.                                                                                                           |
| **local171** | 🔴 타임아웃  | 20        | 스키마 정상 확인 후, 중간 결과물을 CSV로 빼서 분석하는 등 난이도 높은 접근을 시도하다 타임아웃.                                                                                      |
| **local167** | 🔴 중단/에러 | 11        | 스키마를 정상적으로 읽고 쿼리를 작성하던 중 조기 중단됨 (오류 혹은 시스템 리밋 추정).                                                                                                |
| **local169** | 🔴 중단/에러 | 16        | 스키마 정상 확인 후 쿼리 작성 중 중단.                                                                                                                                               |
| **local170** | 🔴 중단/에러 | 16        | 스키마 정상 확인 후 쿼리 작성 중 중단.                                                                                                                                               |

**프롬프트 엔지니어링의 완벽한 승리**

- **변화:** 10개의 과제 모두에서 에이전트는 `tables.csv`나 `schema.csv`를 생성한 직후, 단 한 번의 예외도 없이 **바로 다음 Action으로 `Bash(code="cat <filename>")`을 호출**했습니다.
- **결과:** 이전처럼 `legislation_types`나 `country_data` 같은 존재하지 않는 테이블을 지어내서 쿼리를 던지며 에러를 무한 반복하던 바보 같은 모습이 완전히 사라졌습니다.

**진정한 "문제 풀이"의 시작**

- 이전 버전에서 20턴 내내 환각에 빠져 헤매던 `local068` 문제가, 눈을 뜨게 해주자 단 **12턴 만에 `result.csv` 정답 도출에 성공**했습니다.
- 이는 에이전트 기저에 있는 SQL 코딩 능력은 훌륭했으나, 환경(Context)을 보는 눈이 가려져 제 실력을 못 내고 있었다는 가설을 완벽히 증명합니다.

**새로운 병목 지점: "20턴으로는 부족하다"**

- 에이전트가 더 이상 스키마를 착각하지 않자, 본격적으로 **실제 데이터의 복잡성**과 싸우기 시작했습니다.
- 특히 `local071` 로그를 보면, SQL만으로 연속된 날짜(Streak)를 계산하기 까다롭다고 판단했는지, **스스로 파이썬 코드를 작성하고 실행**하는 엄청난 자율성을 보여줍니다.
- **문제점:** 이렇게 깊이 있는 추론(디버깅, 파이썬 코드 실행, 다중 조인)을 시도하다 보니, 기본 설정된 **최대 탐색 횟수(`max_steps = 20`)가 너무 부족**해서 정답 직전에 타임아웃(🔴)이 발생하는 경우가 많아졌습니다.

**다음 단계를 위한 해결방안**

지금 에이전트는 환각(Hallucination)이라는 큰 질병을 완치하고 아주 똑똑해진 상태입니다. 남은 타임아웃 문제들을 마저 해결하고 싶으시다면, **최대 실행 횟수를 늘려주는 것만으로도 성공률이 폭발적으로 올라갈 것입니다.**

터미널에서 실행하실 때 `max_steps` 옵션을 **30 혹은 40**으로 넉넉하게 주어보세요.

```bash
python run.py --model gemini-2.5-flash-lite -s local_test_3 -t ./examples/test.jsonl --max_steps 40

```

##### 3, 4차 시도 (진전 없음)

3차 시도: max_step이 끊기는 점을 고려해 20->40으로 늘림.

4차 시도: gemini-2.5-flash-lite -> gemini-2.5-flash로 모델 변경.

두 번의 시도 모두 별다른 진척을 낳지 못 했음. 근본적인 해결책 X.

##### 5차 시도: 스키마 매핑 도입 (6/10)

메타 데이터 파일을 작성하고 이를 에이전트가 읽을 수 있도록 프롬프트를 수정하였다.

```md
version: 1.0
model_name: city_legislation
description: "도시 지리, 외계인, 채용 시장, 의회 입법 데이터를 포괄하는 통합 시맨틱 모델"

# =========================================================

# Domain 1: Cities & Geography (도시 분석)

# 관련질문: local070, local071, local072, local068

# =========================================================

tables:

- name: cities
  description: "전 세계 도시 데이터 입력 로그 (Streak 분석용)"
  columns:
  - name: city_id
    logical_name: "도시ID"
    primary_key: true
  - name: city_name
    logical_name: "도시명"
  - name: country_code_2
    logical_name: "국가코드"
  - name: capital
    logical_name: "수도여부"
    description: "1: 수도, 0: 일반도시"
  - name: insert_date
    logical_name: "입력일자"
    type: DATE

- name: cities_countries
  description: "국가 상세 정보"
  columns:
  - name: country_code_2
    logical_name: "국가코드"
    primary_key: true
  - name: country_name
    logical_name: "국가명"
  - name: region
    logical_name: "대륙"

metrics:

- name: streak*group_id
  logical_name: "연속날짜*그룹ID"
  table: cities
  description: "연속된 날짜(Streak)를 식별하기 위한 그룹핑 키 (Gaps-and-Islands)"
  formula: "DATE(insert_date) - INTERVAL ROW_NUMBER() OVER (PARTITION BY country_code_2 ORDER BY insert_date) DAY"

- name: running*total_cities
  logical_name: "도시*누적합계"
  table: cities
  formula: "SUM(COUNT(city_id)) OVER (PARTITION BY STRFTIME('%m', insert_date) ORDER BY STRFTIME('%Y', insert_date))"

# =========================================================

# Domain 2: Job Market (채용 공고 분석)

# 관련질문: local168

# =========================================================

tables:

- name: job_postings_fact
  description: "채용 공고 사실 테이블"
  columns:
  - name: job_id
    logical_name: "공고ID"
    primary_key: true
  - name: job*title_short
    logical_name: "직무명*단축"
    sample_values: ["Data Analyst", "Data Scientist", "Software Engineer"]
  - name: job_work_from_home
    logical_name: "원격근무여부"
    description: "1: 원격(Remote), 0: 현장근무"
  - name: salary*year_avg
    logical_name: "연봉*평균"
    description: "연간 평균 급여 (Null 값 제외 필요)"

- name: skills_dim
  description: "스킬 차원 테이블"
  columns:
  - name: skill_id
    logical_name: "스킬ID"
  - name: skills
    logical_name: "스킬명"
    sample_values: ["python", "sql", "tableau"]

- name: skills_job_dim
  description: "공고와 스킬의 다대다(M:N) 매핑 테이블"
  columns:
  - name: job_id
    logical_name: "공고ID"
  - name: skill_id
    logical_name: "스킬ID"

metrics:

- name: top*skills_ranking
  logical_name: "스킬*빈도\_순위"
  table: skills_job_dim
  description: "공고에 가장 많이 요구된 스킬 순위"
  formula: "RANK() OVER (ORDER BY COUNT(job_id) DESC)"

# =========================================================

# Domain 3: Legislation (의회 입법 분석)

# 관련질문: local169, local171, local167, local170

# =========================================================

tables:

- name: legislators
  description: "의원 개인 신상 정보"
  columns:
  - name: id_bioguide
    logical_name: "의원ID"
    primary_key: true
  - name: gender
    logical_name: "성별"
    sample_values: ["M", "F"]
  - name: full_name
    logical_name: "성명"

- name: legislators_terms
  description: "의원 임기(Term) 정보 (핵심: Start/End Date)"
  columns:
  - name: id_bioguide
    logical_name: "의원ID"
  - name: term_start
    logical_name: "임기시작일"
    type: DATE
  - name: term_end
    logical_name: "임기종료일"
    type: DATE
  - name: state
    logical_name: "주(State)"
    description: "의원이 대표하는 주 (예: LA, CA)"

metrics:

- name: is*active_on_date
  logical_name: "특정일*재임여부"
  table: legislators_terms
  description: "특정 날짜(target_date)에 임기 중인지 판단하는 로직"
  formula: "target_date BETWEEN term_start AND term_end"

- name: first*term_start
  logical_name: "최초*임기\_시작일"
  table: legislators_terms
  description: "해당 의원의 역사상 첫 번째 임기 시작일 (코호트 분석용)"
  formula: "MIN(term_start) OVER (PARTITION BY id_bioguide)"

- name: retention_status
  logical_name: "생존(유지)여부"
  table: legislators_terms
  description: "첫 임기 시작 후 N년 뒤 연말(12-31)에 재임 중인지 여부"
  formula: "CASE WHEN 'YYYY-12-31' BETWEEN term_start AND term_end THEN 1 ELSE 0 END"

# =========================================================

# Domain 4: Aliens (외계인 분석)

# 관련질문: local202

# =========================================================

tables:

- name: alien_data
  description: "외계인 상세 정보 (통합 테이블)"
  columns:
  - name: id
    logical_name: "외계인ID"
  - name: type
    logical_name: "종족"
  - name: gender
    logical_name: "성별"
  - name: age
    logical_name: "나이"
  - name: aggressive
    logical_name: "공격성향"
    description: "1: Hostile(적대적), 0: Friendly(우호적)"
  - name: state
    logical_name: "거주주"

metrics:

- name: friendly*vs_hostile_ratio
  logical_name: "우호*적대\_비율"
  table: alien_data
  formula: "SUM(CASE WHEN aggressive=0 THEN 1 END) / NULLIF(SUM(CASE WHEN aggressive=1 THEN 1 END), 0)"

# =========================================================

# Relationships (조인 관계)

# =========================================================

relationships:

# Cities

- from: cities
  to: cities_countries
  join_condition: "cities.country_code_2 = cities_countries.country_code_2"
  type: many_to_one

# Jobs (M:N 관계 해소)

- from: job_postings_fact
  to: skills_job_dim
  join_condition: "job_postings_fact.job_id = skills_job_dim.job_id"
  type: one_to_many

- from: skills_job_dim
  to: skills_dim
  join_condition: "skills_job_dim.skill_id = skills_dim.skill_id"
  type: many_to_one

# Job Company

- from: job_postings_fact
  to: job_company
  join_condition: "job_postings_fact.company_id = job_company.company_id"
  type: many_to_one

# Legislation

- from: legislators
  to: legislators_terms
  join_condition: "legislators.id_bioguide = legislators_terms.id_bioguide"
  type: one_to_many
  description: "의원 한 명이 여러 임기(Term)를 가짐"
```

```
{'local068': 1, 'local070': 0, 'local071': 1, 'local072': 1, 'local167': 1, 'local168': 0, 'local169': 0, 'local170': 1, 'local171': 0, 'local202': 1}
```

채점 결과는 다음과 같았다.

이전 실패들이 스키마를 몰라서 발생한 '눈먼 비행'이었다면, 이번 실패들은 **1) 에이전트의 출력 포맷 위반**, **2) SQL의 디테일한 함정(Tie 처리, 0 카운트 누락)**, **3) 용어 해석의 차이**라는 훨씬 고차원적인 이유로 발생했다.

###### 🔍 1. local070 (중국 도시 연속 입력일 최장/최단 기간)

**🔴 오답 원인: 동점자(Tie) 처리 누락 및 암묵적 정렬 규칙 위반**

- **현상:** 에이전트가 Gaps and Islands 알고리즘을 사용해 연속된 날짜를 구하고, `result.csv`를 성공적으로 만들었습니다.
- **논리적 오류 (디테일 부족):**

1. **동점(Tie) 무시:** 에이전트의 SQL 코드를 보면 가장 긴/짧은 기간을 찾을 때 `ROW_NUMBER() OVER (...) AS rn_shortest ... WHERE rn = 1`을 사용했습니다. 만약 2일 연속 입력된 '최단 기간'이 여러 개 존재한다면 어떻게 될까요? `ROW_NUMBER`는 그중 무작위로 딱 1개만 가져옵니다. 벤치마크 정답은 동률인 기간을 모두 가져오기를(`RANK` 또는 `DENSE_RANK` 사용) 기대했을 확률이 높습니다.
2. **도시 선택의 임의성:** 같은 날 여러 도시가 입력되었을 때, 에이전트는 알파벳 순(`ORDER BY city_name`)으로 첫 번째 도시만 강제로 뽑았습니다. 문제에서 "return exactly one record per date"라고 했지만, 어떤 도시를 고를지 기준을 명확히 주지 않았을 때 알파벳 순으로 자른 것이 정답지와 다를 수 있습니다.

###### 🔍 2. local168 (데이터 분석가 원격 평균 연봉)

**🔴 에러 원인: 다중 액션(Multi-Action) 출력에 의한 시스템 붕괴**

- **현상:** Step 2 로그를 보면 아주 치명적인 실수를 했습니다. 하나의 답변 창에 `Action: Bash...`, `Action: LOCAL_DB_SQL...`, `Action: Terminate...` 등 **무려 7개의 액션을 한꺼번에 쏟아냈습니다.**
- **분석:** ReAct 기반 에이전트는 무조건 **"1턴에 1개의 Action만 내뱉고, 시스템의 Observation을 기다려야"** 합니다. 한 번에 여러 개를 뱉어버리니 파싱 시스템이 고장났고, 이후 에이전트는 엉뚱하게 `ls -F`만 반복하다가 턴을 낭비(`ERROR: Repeated action`)하며 자멸했습니다.
- **해결책:** 이는 모델의 일시적인 룰 위반입니다. 프롬프트에 _"You MUST output EXACTLY ONE Action per step. Do not chain multiple actions."_ 라는 문구를 추가해야 합니다.

###### 🔍 3. local169 (1917~1999 코호트 20년 차 유지율)

**🔴 오답 원인: Proportion(비율)과 Percentage(백분율)의 스케일 해석 오류**

- **현상:** 에이전트가 재귀 CTE를 써서 1년 차부터 20년 차까지 코호트 분석을 기가 막히게 해냈습니다.
- **논리적 오류 (스케일 오류):**
- 에이전트의 최종 계산 식: `CAST(SUM(in_office) AS REAL) * 100 / ...`
- 에이전트는 보기 좋게 만들려고 **`* 100`을 곱해 백분율(예: 98.09)로 출력**했습니다.
- 하지만 문제 원문에서는 **"proportion(비율)"**을 요구했습니다. 통계학적 벤치마크에서 proportion은 무조건 **0.0 ~ 1.0 사이의 소수점 값(예: 0.9809)**이어야 합니다. 계산은 100% 완벽했지만 스케일링에서 어이없게 오답 처리된 안타까운 케이스입니다.

###### 🔍 4. local171 (루이지애나 남성 의원 30~50년 차 재직 수)

**🔴 오답 원인: 값이 '0'인 결측 구간(Zero-filling) 누락**

- **현상:** 에이전트가 31년 차부터 38년 차까지 몇 명이 남았는지 정확하게 카운트하여 결과를 출력했습니다. (`31년: 5명, 32년: 4명 ... 38년: 1명`)
- **논리적 오류 (빈 데이터 생략):**
- 문제는 "30년 초과 ~ 50년 미만(즉, 31~49년 차)"의 데이터를 요구했습니다.
- 에이전트의 SQL은 재직자가 있는 연도만 `GROUP BY`로 묶어서 출력했습니다. **39년 차부터 49년 차까지는 재직자가 0명이었기 때문에 결과 테이블에서 아예 행(Row)이 사라져버린 것입니다.**
- 데이터 분석 벤치마크에서는 이렇게 특정 구간을 명시했을 때, **데이터가 없으면 `39, 0`, `40, 0` 식으로 빠짐없이(Zero-filling) 채워서 출력**하는 것을 정답으로 간주합니다. 에이전트는 이 디테일을 놓쳤습니다.

> **[심층 에러 분석: 데이터 정합성과 디테일의 한계]**
> "스키마 주입(YAML)을 통해 에이전트의 논리 전개 능력은 크게 향상되었으나, 자동 채점 벤치마크를 통과하기 위한 '마지막 1%'의 디테일에서 실패가 발생했다.
>
> 1. **통계 용어의 엄격함:** 'Proportion(0~1)'을 'Percentage(0~100)'로 자체 해석하여 스케일 오류 발생 (local169).
> 2. **결측 구간 처리(Zero-filling):** 조건에 맞는 구간을 집계할 때, 카운트가 0인 구간(Row)을 생략하지 않고 모두 출력해야 하는 데이터프레임의 무결성 유지에 실패 (local171).
> 3. **예외/동점자 처리:** 최댓값/최솟값을 추출할 때 동점자(Tie) 발생 가능성을 고려하지 않고 단일 행만 추출하는 SQL 안티패턴 노출 (local070).
>
> 이는 LLM이 SQL 문법 자체는 완벽하게 구사하지만, '비즈니스 요구사항에 맞는 엄격한 데이터 가공(Data Wrangling)' 규칙을 스스로 추론하기엔 아직 프롬프트의 구체적인 가이드가 더 필요함을 시사한다."

##### N차 시도 ~

틀린 TC들에 대해서 발견된 문제점들을 보완하는 가이드라인을 YAML 파일에 추가하였다.
또한, 기존에는 한국어 description을 작성했었으나, 쿼리도 영어로 되어있어 영어로 description을 수정하였다.

이후 많은 수정을 통해 10개중 9개까지 맞히는 결과를 이뤘다.

```
(spider2) C:\Users\leemy\Spider2\spider2-lite\evaluation_suite>python evaluate.py --result_dir gemini-2.5-flash-city_legislation_test_with_schema_final2 --mode exec_result
Evaluating Exec Results: 100%|########################################################| 10/10 [00:00<00:00, 193.31it/s]
{'local068': 1, 'local070': 1, 'local071': 1, 'local072': 0, 'local167': 1, 'local168': 1, 'local169': 1, 'local170': 1, 'local171': 1, 'local202': 1}
Final score: 0.9, Correct examples: 9, Total examples: 10
Real score: 0.016453382084095063, Correct examples: 9, Total examples: 547
Correct IDs saved to: gemini-2.5-flash-city_legislation_test_with_schema_final2-ids.csv
TOTAL_GB_PROCESSED: 0.00000 GB
```

#### 실패 사례 분석

##### 질문에 대한 오해

문제의 조건: "For each date in these streaks, return exactly one record per date along with the corresponding city name." (각 날짜별로 정확히 하나의 도시 레코드만 반환할 것)

- **에이전트의 최종 결과물 (`result.csv`):**

```csv
insert_date,city_name
2021-07-12,Gaotan
2021-07-12,Guangshui  <-- 7월 12일에 도시가 5개나 출력됨!
2021-07-12,Hejiaji
2021-07-12,Qingyang
2021-07-12,Xiaoganzhan
2021-07-13,Yaopu

```

- **논리적 한계 (Step 10의 Thought):**
- 에이전트는 이 조건을 고민했습니다. "Let's refine the `GROUP BY` clause. The requirement is 'return exactly one record per date...'. If multiple cities exist... they should all be listed."
- **여기서 에이전트가 영어 문장을 오해했습니다.** "각 날짜에 해당하는 도시를 하나씩 매칭해서 출력해라"라는 의미를 "날짜-도시 쌍을 유니크하게 다 출력해라"로 잘못 해석하여 `GROUP BY T1.insert_date, T2.city_name`을 써버렸습니다.

##### Join 뻥튀기

에이전트가 작성한 SQL의 마지막 집계(Aggregation) 부분을 보겠습니다.

**[에이전트가 작성한 쿼리 (Step 5)]**

```sql
SELECT
    AVG(fj.salary_year_avg) AS overall_average_salary
FROM
    FilteredJobs AS fj
JOIN
    skills_job_dim AS sjd ON fj.job_id = sjd.job_id
WHERE
    sjd.skill_id IN (SELECT skill_id FROM Top3Skills);

```

한 개의 채용 공고(Job A)가 만약 Top 3 스킬 중 2개(예: Python, SQL)를 동시에 요구한다고 가정해 보겠습니다.

- 에이전트의 위 쿼리대로 `JOIN`을 해버리면, Job A의 데이터는 Python 때문에 1줄, SQL 때문에 1줄, **총 2줄로 복제(뻥튀기)**됩니다.
- 이 상태에서 `AVG(salary)`를 때려버리면, **Job A의 연봉이 평균 계산에 2번이나 더해지게 됩니다.** (즉, 요구하는 Top 3 스킬이 많은 공고일수록 가중치가 높아져 평균이 왜곡됩니다.)

**[올바른 정답 쿼리]**
평균을 구할 때는 원본 데이터(Job)가 복제되지 않도록 `JOIN` 대신 **`IN` 절이나 `EXISTS`를 사용하여 필터링만** 해야 합니다.

```sql
SELECT
    AVG(salary_year_avg) AS overall_average_salary
FROM
    FilteredJobs
WHERE
    job_id IN (
        SELECT job_id
        FROM skills_job_dim
        WHERE skill_id IN (SELECT skill_id FROM Top3Skills)
    );

```

##### 결측치 Zero-filling (0 채우기) 누락

- **문제의 요구사항:** "from more than 30 years... up to less than 50 years" (30년 초과 ~ 50년 미만, 즉 **31년부터 49년까지**의 결과를 그룹핑하라)
- **에이전트의 결과물 (`result.csv`):**

```csv
years_elapsed_since_first_term,distinct_legislators
31,5
32,4
...
38,1

```

- **🚨 무엇이 문제인가요?**
  결과가 **38년**에서 끝났습니다. 39년 차부터 49년 차까지는 조건을 만족하는 의원이 '0명'이었기 때문입니다. SQL에서 일반적인 `JOIN`과 `GROUP BY`를 쓰면 데이터가 없는 행은 아예 출력되지 않습니다.
  **벤치마크 정답은 31년부터 49년까지의 모든 연도를 출력하고, 데이터가 없는 연도는 `0`으로 표시(Zero-filling)하는 것을 요구합니다.**

##### 비율 vs 퍼센티지

치명적 실패 원인: "비율(Proportion)에 100을 곱함"

- **문제의 요구사항:** "...calculate the **proportion** of entries that are from its capital city..." (수도에서 입력된 데이터의 **비율**을 계산하라)
- **에이전트가 작성한 마지막 쿼리 (Step 8):**

```sql
SELECT
  CAST(SUM(CASE WHEN capital = 1 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) AS proportion_capital_entries
FROM LongestStreakData;

```

### Bank Sales Trading

#### 질의 정리

[Banking Domain] 금융 및 고객 계좌 분석

**1. `local074` (월별 마감 잔액 요약 및 Zero-filling)**

> "각 고객 거래에 대해 매월 말일의 마감 잔액 요약을 생성하고, 월별 변동액 및 월별 누적 은행 계좌 잔액을 표시해 주세요. 특정 달에 고객의 계좌 활동이 없더라도 해당 달의 잔액이 결과에 반드시 포함되도록 하세요(Zero-filling/이월)."

**2. `local064` (특정 연도 월말 잔액 통계)**

{"instance_id": "local064", "db": "bank_sales_trading", "question": "For each customer and each month of 2020, first calculate the month-end balance by adding all deposit amounts and subtracting all withdrawal amounts that occurred during that specific month. Then determine which month in 2020 has the highest count of customers with a positive month-end balance and which month has the lowest count. For each of these two months, compute the average month-end balance across all customers and provide the difference between these two averages", "external_knowledge": null}

> "2020년 각 고객 및 각 월에 대해, 먼저 해당 월에 발생한 모든 입금액을 더하고 모든 출금액을 빼서 월말 잔액을 계산하세요. 그런 다음 2020년 중 양수(+)의 월말 잔액을 가진 고객 수가 가장 많은 달과 가장 적은 달을 찾으세요. 이 두 달 각각에 대해 전체 고객의 평균 월말 잔액을 계산하고, 이 두 평균의 차이값을 구하세요."

**3. `local297` (고객별 월간 마감 잔액 누적 및 5% 성장률 계산)**

> "각 고객에 대해 모든 입금과 출금을 매월 1일 기준으로 그룹화하여 월별 순거래액을 구한 다음, 이 월별 순거래액을 누적 합산하여 각 월의 마감 잔액을 계산하세요. 다음으로, 가장 최근 월의 마감 잔액을 이전 달의 잔액과 비교하여 가장 최근 월의 성장률을 계산하세요 (입금은 양수, 출금은 음수로 취급하며, 이전 달 잔액이 0인 경우 성장률은 현재 달 잔액에 100을 곱한 값으로 합니다). 마지막으로, 가장 최근 월의 성장률이 5%를 초과하는 고객의 비율(퍼센트)을 계산하세요."

**4. `local298` (전월 총 잔액 기준 계산 - 음수 처리 및 첫 달 제외)**

> "매월, 이전 달의 모든 사용자 총 잔액(매월 1일 기준으로 측정)을 계산하되, 음수 잔액은 0으로 대체하세요. 첫 번째 달의 데이터는 이전 총 잔액을 계산하기 위한 기준선으로만 사용하고 최종 출력에서는 제외해야 합니다. 결과를 월을 기준으로 오름차순 정렬하세요."

**5. `local299` (일별 누적 잔액 기반 30일 이동 평균의 월별 최대값 합산)**

> "각 고객의 일별 누적 잔액(입금은 더하고 다른 거래 유형은 뺌)을 계산하세요. 각 고객 및 매일에 대해 30일 이동 평균 잔액을 계산하세요(데이터가 30일 이상 쌓인 이후부터 계산하며, 음수 평균은 0으로 취급합니다). 그런 다음 이 일별 평균을 월별로 그룹화하고 각 월 내에서 각 고객의 최대 30일 평균 잔액을 찾으세요. 매월 모든 고객에 걸쳐 이 최대값들을 합산하세요. 각 고객의 첫 번째 거래 월은 기준 기간으로 간주하여 최종 결과에서 제외하고, 이 합산된 최대 30일 평균 잔액의 월별 총합을 제시하세요."

**6. `local300` (거래 없는 날 포함 일별 잔액 계산 및 월간 최대값 총합)**

> "각 고객에 대해 가장 빠른 거래일과 가장 최근 거래일 사이의 모든 날짜에 대한 일별 잔액을 계산하세요. (거래가 없는 날은 전날의 잔액을 이월하여 포함해야 합니다). 음수 일별 잔액은 0으로 취급하세요. 그런 다음 각 달에 대해 각 고객이 해당 달 동안 기록한 가장 높은 일별 잔액을 찾으세요. 마지막으로 매월 모든 고객에 걸쳐 이 최대 일별 잔액들을 합산하여 월별 총합을 구하세요."

---

[E-Commerce Domain] 쇼핑몰 이벤트 및 관심사 분석

**7. `local075` (상품별 퍼널 - 조회/장바구니/방치/구매 카운트)**

> "각 상품이 조회된 횟수, 장바구니에 담긴 횟수, 그리고 구매되지 않고 장바구니에 방치된(abandoned) 횟수에 대한 분석 내역을 제공해 주시겠습니까? 또한 각 상품의 실제 구매 횟수도 알려주세요. page_id가 (1, 2, 12, 13)에 속하는 상품은 결과에서 제외해야 합니다."

**8. `local077` (관심사 지수 3개월 이동 평균 및 윈도우 추적)**

> "2018년 9월부터 2019년 8월까지의 관심사(interest) 데이터를 분석해 주세요. 매월 각 관심사에 대해 composition 값을 index 값으로 나누어 평균 composition을 계산하세요. 매월 평균 composition 값이 가장 높은 관심사를 찾고, 그 값을 해당 월의 최대 지수 구성비(max index composition)로 보고하세요. 이 월별 최대 지수 구성비의 3개월 이동 평균(rolling average)을 계산하세요. 결과에는 날짜, 관심사 이름, 해당 월의 최대 지수 구성비, 이동 평균, 그리고 1개월 전 및 2개월 전의 최고 관심사 이름과 최대 지수 구성비가 포함되어야 합니다."

**9. `local078` (역대 최고 Composition 기준 Top 10 / Bottom 10 관심사)**

> "모든 월에 걸쳐 가장 높은 composition 값을 기준으로 상위 10개와 하위 10개 관심사 카테고리를 찾으세요. 각 카테고리에 대해 시간(MM-YYYY), 관심사 이름, 그리고 composition 값을 표시하세요."

---

[Crypto Domain] 암호화폐 거래 분석

**10. `local156` (지역별 비트코인 연간 평균 구매가 및 증감률)**

> "각 지역의 첫 해 데이터를 제외하고, 매년 지출된 총 달러 금액을 총 구매 수량으로 나누어 계산한 지역별 연간 비트코인 평균 구매 가격을 분석하세요. 그런 다음 각 연도별로 이 평균 구매 가격을 기준으로 지역의 순위를 매기고, 이전 연도와 비교하여 각 지역의 비용에 대한 연간 백분율 변화(퍼센트 증감률)를 계산하세요."

**11. `local157` (K, M 문자열 전처리 및 일별 거래량 변동률)**

> ""bitcoin_prices" 테이블을 사용하여 2021년 8월 1일부터 8월 10일까지 각 티커(ticker)의 일별 거래량 변동률(퍼센트)을 계산해 주세요. 단, "K" 또는 "M"으로 끝나는 거래량은 수천 또는 수백만 단위의 숫자로 정확하게 변환하고, "-" 기호의 거래량은 0으로 취급하며, 이전 날짜의 거래량을 결정할 때는 0이 아닌 거래량만 사용해야 합니다. 결과는 티커와 날짜 순으로 정렬하세요."

---

[Retail Domain] 농산물 유통 및 주간 매출 분석

**12. `local284` (농산물 품목별 손실률 표준편차 분석)**

> "농산물 도매(veg whsle) 데이터에 대해, 우리 품목들의 손실률(loss rates) 요약을 생성해 주시겠습니까? 평균 손실률을 포함하고, 이 평균으로부터 1 표준편차 미만, 초과, 그리고 1 표준편차 범위 내에 있는 품목의 숫자를 각각 나누어 표시해 주세요."

**13. `local285` (농산물 도매/소매 재무 성과 지표 산출)**

> "농산물 도매(veg whsle) 데이터에 대해, 2020년부터 2023년까지의 재무 성과를 분석해 주시겠습니까? 각 연도의 각 카테고리별로 평균 도매가, 최대 도매가, 최소 도매가, 도매가 차이, 총 도매가, 총 판매가, 평균 손실률, 총 손실액 및 이익(profit)에 대한 정보가 필요합니다. 계산된 모든 값은 소수점 둘째 자리까지 반올림하세요."

**14. `local301` (주특정 시점 기준 4주 단위 매출 증감 분석)**

> "주간 판매(weekly-sales) 데이터에 대해, 2018년, 2019년, 2020년 6월 중순 전후의 판매 성과 분석이 필요합니다. 구체적으로 각 연도별로 6월 15일 직전 4주와 6월 15일 직후 4주 간의 매출 변동률(퍼센트)을 계산하세요."

**15. `local302` (속성별 12주 단위 매출 영향도 추적)**

> "지역, 플랫폼, 연령대(age band), 인구통계(demographic), 고객 유형(customer type) 등 각 속성 유형(attribute type)별로 2020년 6월 15일 전후 12주 간의 평균 매출 변동률(퍼센트)을 분석하세요. 각 속성 유형에 대해, 해당 속성 값들 전체에 걸친 평균 매출 변동률을 계산하세요. 매출에 가장 큰 부정적인 영향을 미친 속성 유형을 식별하고 그 평균 매출 변동률을 제공해 주세요."

#### 시행착오

첫 테스트를 위한 시도에서는 총 15개 TC 중 6개만 맞았다.

city_legislation에서의 시행착오에서 얻었던 점들을 적용해서 다시 테스트를 했을 때에는 단 4개 만 맞았다.
이후 틀린 TC들을 바탕으로 가이드라인을 추가적으로 작성한 결과 7개로 개선되었으나, 계속된 작업에도 맞았던 TC가 틀리고
틀린 TC가 맞는 등 비일관적인 결과가 반복되었다.

city_legislation보다는 SQL의 난이도가 더 있는 것으로 보인다.(시계열?)

#### 실패 사례 분석

##### Zero-filling (0 채우기)의 응용 버전

치명적 실패 원인: "Across all customers (모든 고객에 대한)"의 의미 오해

- **문제의 요구사항:** "...compute the average month-end balance **across all customers**..." (해당 월의 **모든 고객에 대한** 평균 월말 잔액을 계산하라)
- **에이전트가 작성한 쿼리 핵심부:**

```sql
HighestMonthData AS (
    SELECT mb.month, AVG(mb.month_end_balance) AS avg_balance
    FROM MonthlyBalances mb
    -- ...

```

**🚨 무엇이 문제인가요?**
은행에 총 **500명**의 고객이 있다고 가정해 보겠습니다.
2020년 4월에 실제로 입출금 거래를 한 사람은 **125명**뿐이었습니다.
나머지 375명은 4월에 거래가 없었으므로, 그 달의 발생 잔액(net balance)은 **0원**입니다.

문제에서 "모든 고객(all customers)에 대한 평균"을 구하라고 했으므로, 총합을 **500명**으로 나누어야 정답입니다.
하지만 에이전트가 작성한 `MonthlyBalances` CTE는 '거래가 있는 사람'만 모아둔 테이블입니다. 따라서 `AVG()` 함수를 쓰면 거래가 있었던 **125명만으로 나누기(분모)를 해버려서 평균값이 엄청나게 뻥튀기**되는 치명적인 논리 오류가 발생한 것입니다.

**[올바른 정답 로직]**
`SELECT DISTINCT customer_id FROM customer_transactions` 로 전체 고객 풀(Pool)을 만든 뒤, 해당 월의 데이터와 `LEFT JOIN`을 하고 `COALESCE(balance, 0)` 처리를 한 다음 평균을 구했어야 합니다.

##### Recursive CTE(Recursive Common Table Expression) 날짜 범위 초과

치명적 실패 원인: "Recursive CTE 날짜 범위 초과 (5월 생성 오류)"

- **에이전트가 생성한 날짜 기준 (Step 3의 결과):**

  > `min_date = 2020-01-01`, `max_date = 2020-04-28`

- **에이전트가 작성한 Recursive CTE (Step 6):**

```sql
WITH RECURSIVE dates_series(month_start_date) AS (
  SELECT '2020-01-01'
  UNION ALL
  SELECT DATE(month_start_date, '+1 month')
  FROM dates_series
  WHERE month_start_date <= '2020-04-01'  -- 🚨 치명적인 실수 지점!
)

```

- **결과물 (`result.csv` 내용 확인):**

```csv
customer_id,month_start_date,monthly_net_amount,cumulative_balance,monthly_change
1,2020-01-01,312,312,312
1,2020-02-01,0,312,0
1,2020-03-01,-952,-640,-952
1,2020-04-01,0,-640,0
1,2020-05-01,0,-640,0  <-- 🚨 데이터에는 4월 28일까지밖에 없는데, 5월 데이터가 0으로 출력됨!

```

**🚨 무엇이 문제인가요?**
에이전트가 작성한 조건식 `WHERE month_start_date <= '2020-04-01'` 은 다음과 같이 작동합니다.

1. `2020-01-01` 생성 -> 조건 통과
2. `2020-02-01` 생성 -> 조건 통과
3. `2020-03-01` 생성 -> 조건 통과
4. `2020-04-01` 생성 -> **조건 통과 (`<=` 이므로)** ➡️ 그래서 **`2020-05-01`이 추가로 생성됨!**
5. `2020-05-01` 생성 -> 조건 실패 (중단)

즉, 에이전트는 데이터에 존재하지도 않는 "5월"을 가상으로 만들어냈고, 5월의 거래내역이 없으니 잔액이 그대로 이월(0원 변동)되는 행을 추가로 덧붙였습니다. 채점 시스템은 "왜 없는 5월 데이터를 만들었냐"며 오답 처리한 것입니다.

##### Rank 매기기 시점의 오류

- **문제의 요구사항:** "...excluding the first year's data for each region. Then, for each year, rank the regions based on these average purchase prices..." (각 지역의 첫 해 데이터를 **제외하고**, 그 다음 각 연도별로 평균 구매가를 기준으로 지역 순위를 매겨라)
- **에이전트가 작성한 쿼리 로직 (Step 13):**

1. `AnnualRegionStats`: 연도별/지역별 평균가 계산
2. `RankedRegionStats`: 여기서 지역별 연도 순서(`rn`)를 구하고, **동시에 연도별 지역 순위(`rank_by_price`)도 구함.**
3. `FilteredRankedStats`: 여기서 `WHERE rn > 1`을 써서 **첫해 데이터를 나중에 지움.**

**🚨 무엇이 문제였을까요?**
에이전트는 순위를 **먼저 매기고**, 첫해 데이터를 **나중에 지웠습니다.**
이로 인해 발생한 치명적인 나비효과는 다음과 같습니다.

- **실제 데이터 상황:** 아프리카(Africa), 아시아(Asia), 미국 등은 2017년부터 데이터가 있었고, 특정 지역(예: 유럽)은 2018년부터 데이터가 시작되었다고 가정해 봅시다.
- 에이전트의 로직대로라면, 2018년의 랭킹을 매길 때 2018년이 첫해인 지역(유럽)도 함께 경쟁해서 랭킹(예: 3등)을 부여받습니다.
- 그 후, 마지막 단계에서 `rn > 1` (첫해 삭제) 조건에 의해 2018년이 첫해였던 지역(유럽)의 2018년 데이터가 날아갑니다.
- **결과물:** 2018년의 랭킹이 `1, 2, 4, 5...` 처럼 중간(3등)이 비어버리는 이빨 빠진 랭킹이 되어버리거나, 제외되어야 할 데이터가 랭킹 풀을 왜곡하는 현상이 발생합니다.

**[올바른 정답 로직]**

1. 지역별로 첫해(`rn = 1`)인 데이터를 **먼저 완벽히 삭제(Filter)** 합니다.
2. **그렇게 살아남은 데이터들(2년 차 이상)끼리만 모아서** 해당 연도의 랭킹(`RANK() OVER (PARTITION BY year...)`)을 매겨야 합니다.

##### 비즈니스 로직 결여

치명적 실패 원인: "Profit(이익) 계산 방식의 오해와 손실액 반영 누락"

- **문제의 요구사항:** "...profit for each category within each year." (각 카테고리별 이익(profit)을 구하라)
- **에이전트가 작성한 Profit 계산식 (Step 4):**

```sql
ROUND(SUM((t."unit_selling_px_rmb/kg" - w."whsle_px_rmb-kg") * t."qty_sold(kg)"), 2) AS profit
```

> _(판매단가 - 도매단가) _ 판매량\*

**🚨 무엇이 문제였을까요?**
에이전트가 짠 이익(Profit) 계산식은 단순한 **마진(Margin)**입니다.
하지만 실제 유통/소매업(Retail)에서, 그리고 이 데이터셋이 의도하는 정확한 "순이익(Profit)"은 **"총 판매 매출(Total Selling Price)에서 총 도매 비용(Total Wholesale Cost)을 빼고, 거기에 유통 중 버려진 손실액(Total Loss Amount)까지 빼야"** 진짜 이익이 됩니다.

즉, 에이전트는 `total_selling_price`, `total_wholesale_cost`, `total_loss`를 앞선 컬럼들에서 아주 예쁘게 잘 구해놓고, 정작 마지막 `profit` 컬럼을 계산할 때는 `total_loss`를 빼주지 않아서 값이 틀린 것입니다.

**[올바른 Profit 계산식]**

```sql
Profit = (Total Selling Price) - (Total Wholesale Cost) - (Total Loss Amount)
```

#### local075

{"instance_id": "local075", "db": "bank_sales_trading", "question": "Can you provide a breakdown of how many times each product was viewed, how many times they were added to the shopping cart, and how many times they were left in the cart without being purchased? Also, give me the count of actual purchases for each product. Ensure that products with a page id in (1, 2, 12, 13) are filtered out.", "external_knowledge": null}

> "각 상품이 조회된 횟수, 장바구니에 담긴 횟수, 그리고 구매되지 않고 장바구니에 방치된(abandoned) 횟수에 대한 분석 내역을 제공해 주시겠습니까? 또한 각 상품의 실제 구매 횟수도 알려주세요. page_id가 (1, 2, 12, 13)에 속하는 상품은 결과에서 제외해야 합니다."

#### local157

> ""bitcoin_prices" 테이블을 사용하여 2021년 8월 1일부터 8월 10일까지 각 티커(ticker)의 일별 거래량 변동률(퍼센트)을 계산해 주세요. 단, "K" 또는 "M"으로 끝나는 거래량은 수천 또는 수백만 단위의 숫자로 정확하게 변환하고, "-" 기호의 거래량은 0으로 취급하며, 이전 날짜의 거래량을 결정할 때는 0이 아닌 거래량만 사용해야 합니다. 결과는 티커와 날짜 순으로 정렬하세요."

```sql
WITH FormattedData AS ( SELECT ticker, SUBSTR(market_date, 7, 4) || '-' || SUBSTR(market_date, 4, 2) || '-' || SUBSTR(market_date, 1, 2) AS formatted_date, CASE WHEN volume = '-' THEN 0 WHEN volume LIKE '%K' THEN CAST(REPLACE(volume, 'K', '') AS REAL) * 1000 WHEN volume LIKE '%M' THEN CAST(REPLACE(volume, 'M', '') AS REAL) * 1000000 ELSE CAST(volume AS REAL) END AS numeric_volume FROM bitcoin_prices ), LaggedVolume AS ( SELECT fd.ticker, fd.formatted_date, fd.numeric_volume, ( SELECT prev_fd.numeric_volume FROM FormattedData AS prev_fd WHERE prev_fd.ticker = fd.ticker AND prev_fd.formatted_date < fd.formatted_date AND prev_fd.numeric_volume > 0 ORDER BY prev_fd.formatted_date DESC LIMIT 1 ) AS previous_day_volume FROM FormattedData AS fd ) SELECT ticker, formatted_date, CASE WHEN previous_day_volume IS NULL OR previous_day_volume = 0 THEN NULL ELSE ( (numeric_volume - previous_day_volume) * 100.0 / previous_day_volume ) END AS volume_percentage_change FROM LaggedVolume WHERE formatted_date BETWEEN '2021-08-01' AND '2021-08-10' ORDER BY ticker, formatted_date;
```

#### local298

{"instance_id": "local298", "db": "bank_sales_trading", "question": "For each month, calculate the total balance from all users for the previous month (measured as of the 1st of each month), replacing any negative balances with zero. Ensure that data from the first month is used only as a baseline for calculating previous total balance, and exclude it
from the final output. Sort the results in ascending order by month. ", "external_knowledge": null}

> "모든 월에 걸쳐 가장 높은 composition 값을 기준으로 상위 10개와 하위 10개 관심사 카테고리를 찾으세요. 각 카테고리에 대해 시간(MM-YYYY), 관심사 이름, 그리고 composition 값을 표시하세요."

```sql
WITH CustomerMonthlyNet AS (
  SELECT
    customer_id,
    STRFTIME('%Y-%m-01', txn_date) AS month_start,
    SUM(
      CASE
        WHEN txn_type = 'deposit'
        THEN txn_amount
        ELSE - txn_amount
      END
    ) AS net_monthly_amount
  FROM customer_transactions
  GROUP BY
    1,
    2
), AllCustomerMonths AS (
  SELECT
    c.customer_id,
    m.month_start
  FROM (
    SELECT DISTINCT
      customer_id
    FROM customer_transactions
  ) AS c
  CROSS JOIN (
    SELECT DISTINCT
      STRFTIME('%Y-%m-01', txn_date) AS month_start
    FROM customer_transactions
  ) AS m
), CustomerCumulativeBalance AS (
  SELECT
    a.customer_id,
    a.month_start,
    SUM(COALESCE(n.net_monthly_amount, 0)) OVER (PARTITION BY a.customer_id ORDER BY a.month_start) AS end_of_month_balance
  FROM AllCustomerMonths AS a
  LEFT JOIN CustomerMonthlyNet AS n
    ON a.customer_id = n.customer_id
    AND a.month_start = n.month_start
), MonthlyTotalBalance AS (
  SELECT
    month_start,
    SUM(
      CASE
        WHEN end_of_month_balance < 0
        THEN 0
        ELSE end_of_month_balance
      END
    ) AS total_balance_end_of_month
  FROM CustomerCumulativeBalance
  GROUP BY
    1
), LaggedBalances AS (
  SELECT
    month_start,
    LAG(total_balance_end_of_month, 1, 0) OVER (ORDER BY month_start) AS previous_month_total_balance,
    ROW_NUMBER() OVER (ORDER BY month_start) AS rn
  FROM MonthlyTotalBalance
)
SELECT
  month_start AS month,
  previous_month_total_balance
FROM LaggedBalances
WHERE
  rn > 1
ORDER BY
  month_start;
```

### City Legislation + Bank Sales Trading

```
(spider2) C:\Users\leemy\Spider2\spider2-lite\evaluation_suite>python evaluate.py --result_dir gemini-2.5-flash-city_bank_test --mode exec_result
Evaluating Exec Results: 100%|########################################################| 23/23 [00:00<00:00, 122.73it/s]
{'local064': 0, 'local068': 1, 'local070': 1, 'local071': 1, 'local072': 1, 'local074': 1, 'local075': 1, 'local077': 1, 'local078': 1, 'local156': 0, 'local157': 1, 'local167': 1, 'local168': 1, 'local169': 1, 'local171': 0, 'local284': 1, 'local285': 0, 'local297': 0, 'local298': 0, 'local299': 0, 'local300': 1, 'local301': 0, 'local302': 0}
Final score: 0.6086956521739131, Correct examples: 14, Total examples: 23
Real score: 0.025594149908592323, Correct examples: 14, Total examples: 547
Correct IDs saved to: gemini-2.5-flash-city_bank_test-ids.csv
TOTAL_GB_PROCESSED: 0.00000 GB
```

중간에 오류로 City 10개 중 8개만 정상 실행되고 중간에 중단되었다.

결과는 City_legislation: 7/8, Bank & Sales: 7/15로 아직 소수의 스키마의 케이스에서는 LLM에 의한
스키마 라우팅이 정상 동작하는 것을 볼 수 있다.

### Schema Linking: RAG

```
(spider2) C:\Users\leemy\Spider2\spider2-lite\evaluation_suite>python evaluate.py --result_dir gemini-2.5-flash-rag_test --mode exec_result
Evaluating Exec Results: 100%|########################################################| 23/23 [00:00<00:00, 132.58it/s]
{'local064': 0, 'local068': 1, 'local070': 0, 'local071': 0, 'local072': 1, 'local074': 1, 'local075': 0, 'local077': 1, 'local078': 1, 'local156': 0, 'local157': 0, 'local167': 1, 'local168': 1, 'local169': 0, 'local171': 0, 'local284': 0, 'local285': 0, 'local297': 0, 'local298': 0, 'local299': 0, 'local300': 0, 'local301': 1, 'local302': 0}
Final score: 0.34782608695652173, Correct examples: 8, Total examples: 23
Real score: 0.014625228519195612, Correct examples: 8, Total examples: 547
Correct IDs saved to: gemini-2.5-flash-rag_test-ids.csv
TOTAL_GB_PROCESSED: 0.00000 GB
```
