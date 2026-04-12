## city_legislation

### local168

{"instance_id": "local168", "db": "city_legislation", "question": "Among job postings that specifically have the Data Analyst, require a non-null annual average salary, and are remote, what is the overall average salary when considering only the top three most frequently demanded skills for these positions?", "external_knowledge": null}

대상: 구인 공고 (Job Postings)

조건 1 (직무 및 형태): 직무 타이틀이 **'Data Analyst'**여야 하며, 원격 근무(Remote) 포지션만 대상.

조건 2 (데이터 품질): 연봉 정보(annual average salary)가 비어있지 않은(non-null) 레코드만 포함.

조건 3 (기술 스택 필터): 위 조건에 부합하는 전체 공고 중에서 가장 많이 요구된 **상위 3개의 기술(Skills)**을 식별.

목표 (최종 계산): 식별된 상위 3개 기술 중 최소 하나를 요구하는 공고들의 전체 평균 연봉을 계산.

동점자 처리에 대한 미숙. Top3만 가져와야 하나, 동점처리된 여러 개를 가져오게 됨.

### local169

{"instance_id": "local169", "db": "city_legislation", "question": "What is the annual retention rate of legislators who began their first term between January 1, 1917 and December 31, 1999, measured as the proportion of this cohort still in office on December 31st for each of the first 20 years following their initial term start? The results should show all 20 periods in sequence regardless of whether any legislators were retained in a particular year.", "external_knowledge": null}

분석 대상 (코호트): 1917년 1월 1일부터 1999년 12월 31일 사이에 **생애 첫 임기(First term)**를 시작한 의원들.

측정 지표 (유지율): 위 코호트에 속한 의원들 중, 첫 임기 시작일로부터 이후 1년~20년이 경과한 시점의 매년 12월 31일에 여전히 재직 중인 의원의 비율.

목표: 각 연차별(1년 차~20년 차) 유지율을 순차적으로 계산.

예: (1년 후 12월 31일 재직자 수 / 전체 코호트 인원)

출력 형식: 1년 차부터 20년 차까지의 데이터를 순서대로 나열.

특이사항: 특정 연도에 재직 중인 의원이 없더라도(비율이 0이더라도) 20개의 기간을 모두 빠짐없이 표시해야 함.

프로그래머적 사고 0부터 첫 해를 시작.

## bank_sales_trading

### local064

{"instance_id": "local064", "db": "bank_sales_trading", "question": "For each customer and each month of 2020, first calculate the month-end balance by adding all deposit amounts and subtracting all withdrawal amounts that occurred during that specific month. Then determine which month in 2020 has the highest count of customers with a positive month-end balance and which month has the lowest count. For each of these two months, compute the average month-end balance across all customers and provide the difference between these two averages", "external_knowledge": null}

> "2020년 각 고객 및 각 월에 대해, 먼저 해당 월에 발생한 모든 입금액을 더하고 모든 출금액을 빼서 월말 잔액을 계산하세요. 그런 다음 2020년 중 양수(+)의 월말 잔액을 가진 고객 수가 가장 많은 달과 가장 적은 달을 찾으세요. 이 두 달 각각에 대해 전체 고객의 평균 월말 잔액을 계산하고, 이 두 평균의 차이값을 구하세요."

월말 잔고 = 그달 예금-그달 출금 으로만 생각하고 저번달 잔고를 생각하지 않음.

### local156

{"instance_id": "local156", "db": "bank_sales_trading", "question": "Analyze the annual average purchase price per Bitcoin by region, computed as the total dollar amount spent divided by the total quantity purchased each year, excluding the first year's data for each region. Then, for each year, rank the regions based on these average purchase prices, and calculate the annual percentage change in cost for each region compared to the previous year.", "external_knowledge": null}

> "각 지역의 첫 해 데이터를 제외하고, 매년 지출된 총 달러 금액을 총 구매 수량으로 나누어 계산한 지역별 연간 비트코인 평균 구매 가격을 분석하세요. 그런 다음 각 연도별로 이 평균 구매 가격을 기준으로 지역의 순위를 매기고, 이전 연도와 비교하여 각 지역의 비용에 대한 연간 백분율 변화(퍼센트 증감률)를 계산하세요."

서로다른 데이터셋임을 인지하지 못하고 강제로 통합하려고 함.

**기간먼저 이후 필터링**

### local285

{"instance_id": "local285", "db": "bank_sales_trading", "question": "For veg whsle data, can you analyze our financial performance over the years 2020 to 2023? I need insights into the average wholesale price, maximum wholesale price, minimum wholesale price, wholesale price difference, total wholesale price, total selling price, average loss rate, total loss, and profit for each category within each year. Round all calculated values to two decimal places.", "external_knowledge": null}

> "농산물 도매(veg whsle) 데이터에 대해, 2020년부터 2023년까지의 재무 성과를 분석해 주시겠습니까? 각 연도의 각 카테고리별로 평균 도매가, 최대 도매가, 최소 도매가, 도매가 차이, 총 도매가, 총 판매가, 평균 손실률, 총 손실액 및 이익(profit)에 대한 정보가 필요합니다. 계산된 모든 값은 소수점 둘째 자리까지 반올림하세요."

지속적인 Timeout 발생. 크고 무거운 테이블 2개를 통합하는 과정에서 양쪽에 조인할때 DATE()함수를 씌워버려 timeout.

### local297

{"instance_id": "local297", "db": "bank_sales_trading", "question": "For each customer, group all deposits and withdrawals by the first day of each month to obtain a monthly net amount, then calculate each month\u2019s closing balance by cumulatively summing these monthly nets. Next, determine the most recent month\u2019s growth rate by comparing its closing balance to the prior month\u2019s balance, treating deposits as positive and withdrawals as negative, and if the previous month\u2019s balance is zero, the growth rate should be the current month\u2019s balance multiplied by 100. Finally, compute the percentage of customers whose most recent month shows a growth rate of more than 5%.", "external_knowledge": null}

### local299

{"instance_id": "local299", "db": "bank_sales_trading", "question": "For a bank database with customer transactions, calculate each customer's daily running balance (where deposits add to the balance and other transaction types subtract). For each customer and each day, compute the 30-day rolling average balance (only after having 30 days of data, and treating negative averages as zero). Then group these daily averages by month and find each customer's maximum 30-day average balance within each month. Sum these maximum values across all customers for each month. Consider the first month of each customer's transaction history as the baseline period and exclude it from the final results, presenting monthly totals of these summed maximum 30-day average balances.", "external_knowledge": null}

> "각 고객의 일별 누적 잔액(입금은 더하고 다른 거래 유형은 뺌)을 계산하세요. 각 고객 및 매일에 대해 30일 이동 평균 잔액을 계산하세요(데이터가 30일 이상 쌓인 이후부터 계산하며, 음수 평균은 0으로 취급합니다). 그런 다음 이 일별 평균을 월별로 그룹화하고 각 월 내에서 각 고객의 최대 30일 평균 잔액을 찾으세요. 매월 모든 고객에 걸쳐 이 최대값들을 합산하세요. 각 고객의 첫 번째 거래 월은 기준 기간으로 간주하여 최종 결과에서 제외하고, 이 합산된 최대 30일 평균 잔액의 월별 총합을 제시하세요."

성장률을 구하기 위해 달력의 빈 곳을 0으로 채웠으나, 가장 최근 활동한 달을 최대 날짜인 4월로 착각하게 됨.

### local300

{"instance_id": "local300", "db": "bank_sales_trading", "question": "For each customer, calculate their daily balances for every day between their earliest and latest transaction dates, including days without transactions by carrying forward the previous day's balance. Treat any negative daily balances as zero. Then, for each month, determine the highest daily balance each customer had during that month. Finally, for each month, sum these maximum daily balances across all customers to obtain a monthly total.", "external_knowledge": null}

> "각 고객에 대해 가장 빠른 거래일과 가장 최근 거래일 사이의 모든 날짜에 대한 일별 잔액을 계산하세요. (거래가 없는 날은 전날의 잔액을 이월하여 포함해야 합니다). 음수 일별 잔액은 0으로 취급하세요. 그런 다음 각 달에 대해 각 고객이 해당 달 동안 기록한 가장 높은 일별 잔액을 찾으세요. 마지막으로 매월 모든 고객에 걸쳐 이 최대 일별 잔액들을 합산하여 월별 총합을 구하세요."

날짜/시간 Keyword를 칼럼명으로 써버림.

### local302

{"instance_id": "local302", "db": "bank_sales_trading", "question": "Analyze the average percentage change in sales between the 12 weeks before and after June 15, 2020, for each attribute type: region, platform, age band, demographic, and customer type. For each attribute type, calculate the average percentage change in sales across all its attribute values. Identify the attribute type with the highest negative impact on sales and provide its average percentage change in sales.", "external_knowledge": null}

> "지역, 플랫폼, 연령대(age band), 인구통계(demographic), 고객 유형(customer type) 등 각 속성 유형(attribute type)별로 2020년 6월 15일 전후 12주 간의 평균 매출 변동률(퍼센트)을 분석하세요. 각 속성 유형에 대해, 해당 속성 값들 전체에 걸친 평균 매출 변동률을 계산하세요. 매출에 가장 큰 부정적인 영향을 미친 속성 유형을 식별하고 그 평균 매출 변동률을 제공해 주세요."

unknown, n/a data 무시.
