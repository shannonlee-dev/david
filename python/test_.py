def test_hello_output(capsys):
    """'Hello Mars'가 표준 출력으로 나오는지 검증하는 테스트"""
    print("Hello Mars")
    captured = capsys.readouterr()
    with capsys.disabled():
        print(capsys)

    assert captured.out.strip() == "Hello Mars"