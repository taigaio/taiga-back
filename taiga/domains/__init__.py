# Copyright 2014 Andrey Antukh <niwi@niwi.be>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# y ou may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .base import get_default_domain
from .base import get_domain_for_domain_name
from .base import activate
from .base import deactivate
from .base import get_active_domain
from .base import DomainNotFound

__all__ = ["get_default_domain",
           "get_domain_for_domain_name",
           "activate",
           "deactivate",
           "get_active_domain",
           "DomainNotFound"]
