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
      angular.module('APIMock', ['ngMockE2E'])

      .run(['$httpBackend', function($httpBackend) {
        var jobRecheck = {'job': {'id': 'bar'}};
        var remotecisResp = {'remotecis': []};
        var jobsResp = {'jobs': [{'id': 'foo'}], '_meta': {'count': 1}};
        var jobstatesResp = {'jobstates': []};

        $httpBackend.whenGET(/^\/partials\//).passThrough();
        $httpBackend.whenGET(/\/remotecis\//).respond(remotecisResp);
        $httpBackend.whenGET(/\/jobs\/.*?\/jobstates/).respond(jobstatesResp);
        $httpBackend.whenPOST(/\/jobs\/foo\/recheck/).respond(jobRecheck);
        $httpBackend.whenGET(/\/jobs\/bar/).respond(jobRecheck);
        $httpBackend.whenGET(/\/jobs\//).respond(jobsResp);
      }]);
    });
  });

  beforeEach(function() {
    var cookie = JSON.stringify({
      status: 2,
      team: {name: 'admin'}
    });
    browser.get('/');
    browser.manage().addCookie('user', encodeURIComponent(cookie), '/');
  });

  it('should be possible to recheck a job', function() {
    browser.get('/#/jobs');
    element(by.css('.glyphicon-repeat')).click();
    expect(browser.getLocationAbsUrl()).toMatch('/jobs/bar$');
  });
});
