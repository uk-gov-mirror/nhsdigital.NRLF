"""
Shared utilities for seeding DynamoDB tables with pointer data.
"""

# NHS number checksum weights (10, 9, 8, 7, 6, 5, 4, 3, 2)
CHECKSUM_WEIGHTS = list(range(10, 1, -1))


class TestNhsNumbersIterator:
    """Iterator that generates valid NHS numbers with proper checksums."""

    def __iter__(self):
        self.first9 = 900000000
        return self

    def __next__(self):
        if self.first9 > 999999999:
            raise StopIteration
        checksum = 10
        while checksum == 10:
            self.first9 += 1
            nhs_no_digits = list(map(int, str(self.first9)))
            checksum = (
                sum(
                    weight * digit
                    for weight, digit in zip(CHECKSUM_WEIGHTS, nhs_no_digits)
                )
                * -1
                % 11
            )
        nhs_no = str(self.first9) + str(checksum)
        return nhs_no
