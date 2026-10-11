@wip
Feature: Users can count
  A signed-in user adds to their own count. A sample feature: replace
  it with the application's own.

  Background:
    Given the application is up

  Scenario: A user's count starts at zero and goes up
    Given "alice" is an authenticated user
    When "alice" does an `increment` with `amount=3` on `User` of "alice"
    Then as "alice", `get` on the `User` for "alice" has `value=3`
