angular.module('showSortJuniorApp', [])

.controller('mainController', function($scope, $http) {
  $scope.tableSelect = 'basic_stats';   // default table
  $scope.statsSortCriterion = 'points'; // default sort criterion
  $scope.statsSortDescending = true;    // descending as default sort order
  $scope.nameFilter = '';               // empty name filter
  $scope.hideOveragers = false;         // per default overagers are shown

  // changing displayed table according to selected value 
  $scope.selectChange = function() {
    if ($scope.tableSelect === 'basic_stats') {
      $scope.statsSortCriterion = '';
    } else if ($scope.tableSelect === 'additional_stats') {
      $scope.statsSortCriterion = '';
    } else if ($scope.tableSelect === 'player_information') {
      $scope.statsSortCriterion = '';
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

  // loading stats from external json file
  $http.get('junior.json').then(function(res) {
      $scope.last_modified = res.data[0]['last_modified'];
      $scope.stats = res.data.slice(1);
  });

});