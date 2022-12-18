import os

from configurator import Configurator
from gtest import prepare_google_test_runner
from fake_test import FakeTestRunner


def configure(build_dir, dry_run):
    # Глобальные настройки тестирования
    config = Configurator(
        # Если общее время тестирования решения превысит `overall_tl_sec`,
        # тестирование будет остановлено, а решение получит TLE и 0 баллов.
        overall_tl_sec=480,
        # Максимальное время тестирования на одном тесте по умолчанию.
        # Для более длительных тестов лимит по времени можно задать с помощью
        # `override_time_limit`.
        default_time_limit_sec=1,
        # Ограничение по памяти по умолчанию. Лимиты для определённых тестов
        # задаются с помощью `override_memory_limit`.
        # !!! ВАЖНО !!! Ограничения по памяти носят статус экспериментальных,
        # механизм не протестирован и его работоспособность не гарантируется.
        default_memory_limit_kb=None,
    )

    # Добавление исполняемого файла с тестами на основе Google Test
    gtest_runner = prepare_google_test_runner(
        dry_run=dry_run,
        # Базовое имя исполняемого файла (из build.sh)
        test_binary_path=os.path.join(build_dir, 'tests'),
        # Постфиксы исполняемых файлов с тестами, которые следует запускать
        # в общем случае
        editions=('_opt', '_asan', '_dbg',),
        # Постфиксы исполняемых файлов с тестами, которые следует запускать
        # для тестов, помеченных тегом "heavy" (см. `mark_heavy_*`)
        heavy_tests_editions=('_opt',),
        # Количество запусков каждого из тестов на каждом из постфиксов.
        # Если хотя бы один из запусков падает, тест не засчитывается.
        # Данный механизм позволяет иногда словить недетерминированное поведение
        # решений.
        runs_count=2,
    )
    # Перечень тестов, для которых тестирование проходит на ограниченном наборе
    # конфигураций компилятора. Сюда следует включать тесты:
    # - в которых происходит проверка скорости работы решения;
    # - чрезвычайно долгие тесты, где можно пожертвовать полнотой проверки.
    gtest_runner.mark_heavy_suit('.*Speed.*')
    config.load_runner(gtest_runner)

    # Начисление бонусных баллов "за полное решение" реализуется путём создания
    # "пустых тестов" (`FakeTestRunner`), установке этим тестов бонусных баллов
    # и добавлением зависимостей от всех тестов задачи к соответствующему
    # бонусному тесту (`add_dependency`). При этом, для того, чтобы учащиеся
    # всегда видели результаты по каждому из бонусов в отдельности, а не скрытую
    # за `FullSolutionBonus.*` сумму, необходимо поставить им соответствующую
    # метку с помощью `mark_standalone_tests`.
    config.load_runner(
        FakeTestRunner([
            ('FullSolutionBonus', 'Bonus'),
        ])
    )
    config.add_private_test('FullSolutionBonus', 'Bonus', 17)
    config.add_dependency('FullSolutionBonus\\.Bonus', 'Samples\\.*')
    config.add_dependency('FullSolutionBonus\\.Bonus', 'Foo\\.*')
    config.add_dependency('FullSolutionBonus\\.Bonus', 'Bar\\.*')
    config.mark_standalone_tests('FullSolutionBonus\\..*')

    # Пример установки повышенного лимита по времени на определённые тесты
    config.override_time_limit('YetAnotherPrivateGroup\\.Test.*', 30)

    # Имеется возможность полностью исключить некоторые тесты, несмотря на их
    # наличие в исходниках и итоговом бинарнике. Используется в случаях, если
    # в очередном году Вы не хотите давать какую-то из задач, но тесты к ней
    # удалять тоже не хотите (вдруг, через год снова дадите).
    config.skip_group("SomeOldTestSuite.*")

    # 'public' testset:
    #   config.add_public_suit('SuitName')
    #   config.add_public_test('SuitName', 'TestName')
    #   config.add_public_group('SuitName\\.Test.*')

    config.add_public_test('Samples', 'Test1')
    config.add_public_test('Samples', 'Test2')
    config.add_public_test('Samples', 'Test3')
    config.add_dependency('Samples.Test3', 'Samples.Test2')
    config.mark_standalone_tests('Samples\\..*')

    # 'private' testset:
    #   config.add_private_suit('SuitName', score)
    #   config.add_private_test('SuitName', 'TestName', score)
    #   config.add_private_group('SuitName\\.Test.*', score)

    config.add_private_suit('Foo', 4)
    config.add_private_suit('Bar', 2)
    config.add_private_suit('SomeFunc', 3)
    config.add_private_suit('YetAnotherPrivateGroup', 1)
    config.mark_standalone_tests('YetAnotherPrivateGroup\\.Test2')

    # Если тестов ооочень много и подгонять под круглую сумму вручную не
    # хочется, можно воспользоваться вспомогательной функцией, выполняющей
    # масштабирование баллов под нужную сумму.
    #config.normalize_scores(150)

    # Временный пропуск определённых тестов.
    # Используется в случае, когда изначально нужно показывать результаты лишь
    # на некоторых из тестов (например, если какая-то из задач по условию
    # отправляется "вслепую"). При использовании такого способа пропуска тестов,
    # во-первых, отправляющие всё ещё могут узнать вердикт **компиляции** для
    # нетестируемых групп и, во-вторых, все выставляемые через групповые
    # операции баллы не будут изменены относительно итоговых.
    #
    # Если `reverse_filter=True`, то будут пропущены все тесты, за исключением
    # подпадающих под указанное регулярное выражение. В противном случае тесты,
    # подпадающие под регулярное выражение, будут пропущены.
    #
    #config.force_skip_group(".*(Foo|Bar).*", reverse_filter=False)

    return config
