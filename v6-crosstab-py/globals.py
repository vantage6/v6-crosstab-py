# The following global variables are algorithm settings. They can be overwritten by
# the node admin by setting the corresponding environment variables.

# Minimum value to be given as individual value in the contingency table. To be
# overwritten by setting the "CROSSTAB_PRIVACY_THRESHOLD" environment variable.
DEFAULT_PRIVACY_THRESHOLD = "5"

# Minimum number of rows in the node's dataset. To be overwritten by setting the
# "CROSSTAB_MINIMUM_ROWS_TOTAL" environment variable.
DEFAULT_MINIMUM_ROWS_TOTAL = "5"

# Whether or not to allow value of 0 in the contingency table. To be overwritten by
# setting the "CROSSTAB_ALLOW_ZERO" environment variable.
DEFAULT_ALLOW_ZERO = "false"
