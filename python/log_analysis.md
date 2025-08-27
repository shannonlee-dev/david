# 사고 원인 분석 보고서

## 1) 사건 개요
- 분석 대상: mission_computer_main.log
- 분석 범위: 2023-08-27 10:00:00 ~ 2023-08-27 12:00:00

## 2) 요약 지표
- (로그 수준 식별 실패: 패턴 비일치 가능)

## 3) 상위 메시지(빈도)
- 1× INFO,Center and mission control systems powered down.
- 1× INFO,Oxygen tank explosion.
- 1× INFO,Oxygen tank unstable.
- 1× INFO,Mission completed successfully. Recovery team dispatched.
- 1× INFO,Touchdown confirmed. Rocket safely landed.

## 4) 잠정 원인 가설
- 심각도 높은 항목이 적어 환경/설정 변경, 일시적 부하 가능성 검토.

## 5) 근거 샘플 (상위 5개)
> 2023-08-27 12:00:00 INFO,Center and mission control systems powered down.
> 2023-08-27 11:40:00 INFO,Oxygen tank explosion.
> 2023-08-27 11:35:00 INFO,Oxygen tank unstable.
> 2023-08-27 11:30:00 INFO,Mission completed successfully. Recovery team dispatched.
> 2023-08-27 11:28:00 INFO,Touchdown confirmed. Rocket safely landed.

## 6) 대응 및 재발 방지
- 즉각 조치: 서비스 재시작/롤백/임시 타임아웃 상향 등 영향 축소
- 장기 대책: 재시도·서킷브레이커·지표/알람 추가, 에러 메시지 표준화
