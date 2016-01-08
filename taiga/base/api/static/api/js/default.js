/*
 * Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
 * Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
 * Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
 * Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * The code is partially taken (and modified) from django rest framework
 * that is licensed under the following terms:
 *
 * Copyright (c) 2011-2014, Tom Christie
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.
 * Redistributions in binary form must reproduce the above copyright notice, this
 * list of conditions and the following disclaimer in the documentation and/or
 * other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

function getCookie(c_name)
{
    // From http://www.w3schools.com/js/js_cookies.asp
    var c_value = document.cookie;
    var c_start = c_value.indexOf(" " + c_name + "=");
    if (c_start == -1) {
        c_start = c_value.indexOf(c_name + "=");
    }
    if (c_start == -1) {
        c_value = null;
    } else {
        c_start = c_value.indexOf("=", c_start) + 1;
        var c_end = c_value.indexOf(";", c_start);
        if (c_end == -1) {
            c_end = c_value.length;
        }
        c_value = unescape(c_value.substring(c_start,c_end));
    }
    return c_value;
}

// JSON highlighting.
prettyPrint();

// Bootstrap tooltips.
$('.js-tooltip').tooltip({
    delay: 1000
});

// Deal with rounded tab styling after tab clicks.
$('a[data-toggle="tab"]:first').on('shown', function (e) {
    $(e.target).parents('.tabbable').addClass('first-tab-active');
});
$('a[data-toggle="tab"]:not(:first)').on('shown', function (e) {
    $(e.target).parents('.tabbable').removeClass('first-tab-active');
});

$('a[data-toggle="tab"]').click(function(){
    document.cookie="tabstyle=" + this.name + "; path=/";
});

// Store tab preference in cookies & display appropriate tab on load.
var selectedTab = null;
var selectedTabName = getCookie('tabstyle');

if (selectedTabName) {
    selectedTab = $('.form-switcher a[name=' + selectedTabName + ']');
}

if (selectedTab && selectedTab.length > 0) {
    // Display whichever tab is selected.
    selectedTab.tab('show');
} else {
    // If no tab selected, display rightmost tab.
    $('.form-switcher a:first').tab('show');
}
