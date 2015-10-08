// -*- coding: utf-8 -*-
//
// Copyright 2015 Red Hat, Inc.
//
// Licensed under the Apache License, Version 2.0 (the 'License'); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

'use strict';

module.exports = angular.module('app', [
  'ngCookies', 'angular-loading-bar', 'ui.router', 'googlechart', 'ngResource'
])

.controller('StatsController', [
  '$scope', '$stateParams', '$resource', '$cookies', '$state', 'CommonCode',
  function($scope, $stateParams, $resource, $cookies, $state, CommonCode) {
    var Products = $resource('/api/products').get();
    Products.$promise.then(function(products) {
      $scope.products = products._items;
      $scope.currentProduct = products._items[0];

      var Versions = $resource('/api/versions').get(
        {'where': {'product_id': $scope.currentProduct.id}});
        Versions.$promise.then(function(versions) {
          $scope.versions = versions._items;
          $scope.currentVersion = versions._items[0];
        });
    });

    var getRate = function(product_id, version_id) {
      var Remotecis = $resource('/api/remotecis').get({
        'extra_data': 1, 'version_id': version_id
      });

      Remotecis.$promise.then(function(remotecis) {
        $scope.chart = {
          'type': 'PieChart',
          'data': [],
          'options': {
            'displayExactValues': true,
            'width': 600,
            'height': 400,
            'chartArea': {'left': 10, 'top': 10, 'bottom': 0, 'height': '100%'}
          },
          'formatters': {},
          'displayed': true
        };

        $scope.chart.data = [
          ['Status', 'rate'],
          ['Success', remotecis.extra_data.success],
          ['Failure', remotecis.extra_data.failure],
          ['Ongoing', remotecis.extra_data.ongoing],
          ['Not started', remotecis.extra_data.not_started]
        ];

      });
    }

    $scope.$watch('currentProduct', function(currentProduct, previousProduct) {
      if (angular.isUndefined(currentProduct)) {
        return;
      }

      var Versions = $resource('/api/versions').get({
        'where': {'product_id': currentProduct.id}
      });

      Versions.$promise.then(function(versions) {
        $scope.versions = versions._items;
        $scope.currentVersion = versions._items[0];
      });
    });

    $scope.$watch('currentVersion', function(currentVersion, previousVersion) {
      if (
        angular.isUndefined(currentVersion) ||
        angular.isUndefined($scope.currentProduct)
      ) { return; }

      getRate($scope.currentProduct.id, currentVersion.id);
    });
  }
]);

