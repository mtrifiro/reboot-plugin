@wip
Feature: Users can count
  A user creates a counter and adds to it. A sample feature: replace
  it with the application's own.

  Background:
    Given the application is up

  Scenario: A new counter counts up from zero
    Given "alice" is an authenticated user
    When "alice" does a `create_counter` on `User` of "alice"
    And the resulting `counter_id` is saved as "counter id"
    And "alice" does an `increment` with `amount=3` on `Counter` of "<counter id>"
    Then as "alice", `get` on the `Counter` for "<counter id>" has `value=3`
