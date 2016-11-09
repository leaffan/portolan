angular.module('showSortJuniorApp', [])

.controller('mainController', function($scope, $http) {

  // loading stats from external json file
  $http.get('junior.json').then(function(res) {
      $scope.last_modified = res.data[0]['last_modified'];
      $scope.stats = res.data.slice(1);
  });

});