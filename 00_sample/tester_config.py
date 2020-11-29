import os

from configurator import Configurator
from fake_test import FakeTestRunner
from gtest import prepare_google_test_runner


def configure(build_dir, dry_run):
    config = Configurator(
        overall_tl_sec=600,
        default_time_limit_sec=10,
        default_memory_limit_kb=None,
    )

    # Add test binary
    config.load_runner(
        prepare_google_test_runner(
            os.path.join(build_dir, 'tests'),
            dry_run=dry_run,
            editions=['_opt', '_asan', '_dbg'],
            # editions=['_opt', '_msan', '_asan', '_dbg'],
            runs_count=2,
        )
    )

    # Add fake tests (bonus scores)
    config.load_runner(
        FakeTestRunner([
            ('FullSolutionBonus', 'Bonus'),
        ])
    )

    # Set special resource limits for certain tests
    config.override_time_limit('YetAnotherPrivateGroup\\.Test.*', 30)

    # Define 'public' testset:
    #   config.add_public_suit('SuitName')
    #   config.add_public_test('SuitName', 'TestName')
    #   config.add_public_group('SuitName\\.Test.*')

    config.add_public_test('Samples', 'Test1')
    config.add_public_test('Samples', 'Test2')
    config.add_public_test('Samples', 'Test3')
    config.add_dependency('Samples.Test3', 'Samples.Test2')
    config.mark_standalone_tests('Samples\\..*')

    # Define scores for 'private' testset:
    #   config.add_private_suit('SuitName', score)
    #   config.add_private_test('SuitName', 'TestName', score)
    #   config.add_private_group('SuitName\\.Test.*', score)

    config.add_private_suit('Foo', 4)
    config.add_private_suit('Bar', 2)
    config.add_private_suit('SomeFunc', 3)
    config.add_private_suit('YetAnotherPrivateGroup', 1)
    config.mark_standalone_tests('YetAnotherPrivateGroup\\.Test2')

    # Bonus score for full solution
    config.add_private_group('FullSolutionBonus\\.*', 17)
    config.add_dependency('FullSolutionBonus\\..*', 'Samples\\.*')
    config.add_dependency('FullSolutionBonus\\..*', 'Foo\\.*')
    config.add_dependency('FullSolutionBonus\\..*', 'Bar\\.*')
    config.mark_standalone_tests('FullSolutionBonus\\..*')

    # Scaling the scores to achieve the specific total sum
    config.normalize_scores(100)

    return config
