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

/*globals describe, it, expect, element, browser*/
describe('DCI homepage', function() {
  beforeEach(function() {
    browser.addMockModule('APIMock', function() {
      angular
      .module('APIMock', ['ngMockE2E'])
      .run(['$httpBackend', function($httpBackend) {
        $httpBackend.whenGET(/^\/partials\//).passThrough();
        $httpBackend.whenGET(/^\/api\/jobstates/).respond(function() {
          return [200, {_items: []}, {}];
        });

        $httpBackend.whenGET(/^\/api\/jobs\/1234/).respond(function() {
          return [200, {id: 1234, remoteci: {id: 1234}}, {}];
        });

        $httpBackend.whenPOST(/^\/api\/jobs/).respond(function() {
          return [200, {id: 5678}, {}];
        });
        $httpBackend.whenGET(/^\/api\/jobs\/5678/).respond(function() {
          return [200, {}, {}];
        });
      }]);
    });
  });

  beforeEach(function() {
    browser.get('/');
    browser.manage().addCookie('token', 'sometoken', '/');
  });

  xit('should be possible to recheck a job', function() {
    browser.get('/#/jobs/1234');
    element(by.css('.glyphicon-repeat')).click();
    expect(browser.getLocationAbsUrl()).toBe('/jobs/5678');
  });
});
