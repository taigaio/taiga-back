# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from rest_framework import serializers

import reversion

from taiga.base.serializers import PickleField

from . import models


class QuestionSerializer(serializers.ModelSerializer):
    tags = PickleField()
    comment = serializers.SerializerMethodField("get_comment")
    history = serializers.SerializerMethodField("get_history")
    is_closed = serializers.Field(source="is_closed")

    class Meta:
        model = models.Question
        fields = ()

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_questions_diff(self, old_question_version, new_question_version):
        old_obj = old_question_version.field_dict
        new_obj = new_question_version.field_dict

        diff_dict = {
            "modified_date": new_obj["modified_date"],
            "by": old_question_version.revision.user,
            "comment": old_question_version.revision.comment,
        }

        for key in old_obj.keys():
            if key == "modified_date":
                continue

            if old_obj[key] == new_obj[key]:
                continue

            diff_dict[key] = {
                "old": old_obj[key],
                "new": new_obj[key],
            }

        return diff_dict

    def get_history(self, obj):
        diff_list = []
        current = None

        if obj:
            for version in reversed(list(reversion.get_for_object(obj))):
                if current:
                    questions_diff = self.get_questions_diff(current, version)
                    diff_list.append(questions_diff)

                current = version

        return diff_list
