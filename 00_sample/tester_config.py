import os

from gtest_wrapper import prepare_gtest_binary_wrapper
from tester import Configurator


def configure(build_dir, dry_run=False):
    config = Configurator()

    # Define the testing logic
    config.load_google_binary(
        prepare_gtest_binary_wrapper(
            os.path.join(build_dir, 'tests'),
            dry_run=dry_run,
            editions=['_opt', '_asan', '_dbg'],
            # editions=['_opt', '_msan', '_asan', '_dbg'],
            runs_count=2,
        )
    )

    # Define 'public' testset
    # config.add_public_suit('SuitName')
    # config.add_public_test('SuitName', 'TestName')
    # config.add_public_group('SuitName\\.Test.*')

    # Define scores for 'private' testset
    # config.add_private_suit('SuitName', 3)
    # config.add_private_test('SuitName', 'TestName', 3)
    # config.add_private_group('SuitName\\.Test.*', 3)

    config.add_public_test('Samples', 'Test1')
    config.add_public_test('Samples', 'Test2')
    config.add_public_test('Samples', 'Test3')
    config.add_dependency('Samples.Test3', 'Samples.Test2')

    config.add_private_suit('Foo', 4)
    config.add_private_suit('Bar', 2)
    config.add_private_suit('SomeFunc', 3)
    config.add_private_suit('YetAnotherPrivateGroup', 1)

    # Show per-test report for the following test suits
    config.add_detailed_suits('Samples')
    config.add_detailed_suits('YetAnotherPrivateGroup')

    # Scaling the scores to achieve the specific total sum
    config.normalize_scores(100)

    return config
