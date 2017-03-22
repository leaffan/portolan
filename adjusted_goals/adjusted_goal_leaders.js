angular.module('adjustedGoalLeadersApp', [])

.controller('mainController', function($scope, $http) {

    $scope.sortCriterion = 'adjusted_goals_per_season';
    // default sort order is descending
    $scope.statsSortDescending = true;


    // setting column sort order according to current and new sort criteria, and current sort order 
    $scope.setSortOrder = function(sortCriterion, oldSortCriterion, oldStatsSortDescending) {
        // if current criterion equals the new one
        if (oldSortCriterion === sortCriterion) {
            // just change sort direction
            return !oldStatsSortDescending;
        } else {
            // ascending for a few columns
            if (['last_name'].indexOf(sortCriterion) !== -1) {
                return false;
            } else {
                // otherwise descending sort order
                return true;
            }
        }
    };

    $scope.careerGoalFilter = function(a) {
        if ($scope.goalFilter) {
            if (a.sum_goals < $scope.goalFilter) {
                return false;
            }
            else {
                return true;
            }
        } else {
            return true;
        }
    }

    $scope.gamesPlayedFilter = function(a) {
        if ($scope.gameFilter) {
            if (a.sum_games < $scope.gameFilter) {
                return false;
            }
            else {
                return true;
            }
        } else {
            return true;
        }
    }

    // $scope.setTextColor = function (val) {
    //     var isRed = false;
    //     if (val < 0) {
    //         isRed = true;
    //     }

    //     return isRed;
    // };

    // loading stats from external json file
    $http.get('adjusted_goal_data.json').then(function(res) {
        $scope.stats = res.data;
    });

});