###
# Copyright (c) 2011, Valentin Lorentz
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import json
import urllib

import git

import supybot.log as log
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('PluginDownloader')

class Repository:
    pass

class VersionnedRepository(Repository):
    pass

class GitRepository(VersionnedRepository):
    pass

class GithubRepository(GitRepository):
    def __init__(self, username, reponame, path='/'):
        self._username = username
        self._reponame = reponame
        self._path = [x for x in path.split('/') if x != '']
        

    _apiUrl = 'http://github.com/api/v2/json'
    def _query(self, type_, uri_end, args={}):
        args = dict([(x,y) for x,y in args.items() if y is not None])
        url = '%s/%s/%s?%s' % (self._apiUrl, type_, uri_end,
                               urllib.urlencode(args))
        return json.load(utils.web.getUrlFd(url))

    def getPluginList(self):
        latestCommit = self._query(
                                  'repos',
                                  'show/%s/%s/branches' % (
                                                          self._username,
                                                          self._reponame,
                                                          )
                                  )['branches']['master']
        treeHash = self._navigate(latestCommit, self._path)
        if treeHash is None:
            log.error((
                      'Cannot get plugins list from repository %s/%s '
                      'at Github'
                      ) % (self._username, self._reponame))
            return []
        nodes = self._query(
                           'tree',
                           'show/%s/%s/%s' % (
                                             self._username,
                                             self._reponame,
                                             treeHash,
                                             )
                           )['tree']
        plugins = [x['name'] for x in nodes if x['type'] == 'tree']
        return plugins

    def _navigate(self, treeHash, path):
        if path == []:
            return treeHash
        tree = self._query(
                          'tree',
                          'show/%s/%s/%s' % (
                                            self._username,
                                            self._reponame,
                                            treeHash,
                                            )
                          )['tree']
        nodeName = path.pop(0)
        for node in tree:
            if node['name'] != nodeName:
                continue
            if node['type'] != 'tree':
                return None
            else:
                return self._navigate(node['sha'], path)
                # Remember we pop(0)ed the path
        return None

repositories = {
               'ProgVal': GithubRepository('ProgVal', 'Supybot-plugins'),
               'quantumlemur': GithubRepository(
                                               'quantumlemur',
                                               'Supybot-plugins'
                                               ),
               }

class PluginDownloader(callbacks.Plugin):
    """Add the help for "@plugin help PluginDownloader" here
    This should describe *how* to use this plugin."""

    @internationalizeDocstring
    def repolist(self, irc, msg, args, repository):
        """[<repository>]

        Displays the list of plugins in the <repository>.
        If <repository> is not given, returns a list of available
        repositories."""

        global repositories
        if repository is None:
            irc.reply(_(', ').join([x for x in repositories]))
        else:
            plugins = repositories[repository].getPluginList()
            if plugins == []:
                irc.error(_('No plugin found in this repository.'))
            else:
                irc.reply(_(', ').join([x for x in plugins]))
    repolist = wrap(repolist, [optional('something')])


PluginDownloader = internationalizeDocstring(PluginDownloader)
Class = PluginDownloader


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
