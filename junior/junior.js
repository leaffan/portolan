angular.module('showSortJuniorApp', [])

.controller('mainController', function($scope, $http) {
    // default table selection and sort criterion for skater page
    $scope.skaterTableSelect = 'skater_basic_stats';
    $scope.skaterSortCriterion = 'points';
    // default table selection and sort criterion for goalie page
    $scope.goalieTableSelect = 'goalie_basic_stats';
    $scope.goalieSortCriterion = 'save_percentage';
    // default sort order is descending
    $scope.statsSortDescending = true;
    // default filter values
    $scope.nameFilter = ''; // empty name filter
    $scope.hideOveragers = false; // per default overagers are shown
    $scope.hideUshlPlayers = false; // per default USHL players are shown

    // changing table displayed on skater page according to selected value
    $scope.changeSkaterTable = function() {
        if ($scope.skaterTableSelect === 'skater_basic_stats') {
            $scope.skaterSortCriterion = 'points';
        } else if ($scope.skaterTableSelect === 'skater_additional_stats') {
            $scope.skaterSortCriterion = 'power_play_points';
        } else if ($scope.skaterTableSelect === 'skater_information') {
            $scope.skaterSortCriterion = 'dob';
        }
    };

    // changing table displayed on goalie page according to selected value
    $scope.changeGoalieTable = function() {
        if ($scope.goalieTableSelect === 'goalie_basic_stats') {
            $scope.goalieSortCriterion = 'save_percentage';
        } else if ($scope.goalieTableSelect === 'goalie_additional_stats') {
            $scope.goalieSortCriterion = 'wins';
        } else if ($scope.goalieTableSelect === 'goalie_information') {
            $scope.goalieSortCriterion = 'dob';
        }
    };

    // hiding overagers if corresponding checkbox is checked
    $scope.overageFilterFunc = function(a) {
        if ($scope.hideOveragers && a.is_overager) {
            return false;
        } else {
            return true;
        }
    };

    // hiding USHL players if corresponding checked is checked
    $scope.ushlFilterFunc = function(a) {
        if ($scope.hideUshlPlayers && a.league === 'USHL') {
            return false;
        } else {
            return true;
        }
    }

    // setting column sort order according to current and new sort criteria, and current sort order 
    $scope.setSortOrder = function(sortCriterion, oldSortCriterion, oldStatsSortDescending) {
        // if current criterion equals the new one
        if (oldSortCriterion === sortCriterion) {
            // just change sort direction
            return !oldStatsSortDescending;
        } else {
            // ascending for a few columns
            if (['last_name', 'team[2]', 'league', 'shoots', 'position', 'draft_day_age', 'country', 'goals_against_average'].indexOf(sortCriterion) !== -1) {
                return false;
            } else {
                // otherwise descending sort order
                return true;
            }
        }
    };

    // loading skater stats from external json file
    $http.get('junior.json').then(function(res) {
        $scope.last_modified = res.data[0]['last_modified'];
        $scope.stats = res.data.slice(1);
    });

    // loading goalie stats from external json file
    $http.get('junior_goalies.json').then(function(res) {
        $scope.goalies_last_modified = res.data[0]['last_modified'];
        $scope.goalie_stats = res.data.slice(1);
    });

});