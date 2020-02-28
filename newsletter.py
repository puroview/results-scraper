import os
import jinja2
from datetime import datetime, timedelta
from itertools import groupby

from gcloud import Storage
import db
import notifier


class Newsletter:
    def __init__(self, rendered_filename):
        dates = [datetime.today() - timedelta(days=x) for x in range(7)]
        self.date_list = []
        for i in reversed(dates):
            date = i.date().strftime('%d.%m.%Y')
            self.date_list.append(date)

        self.template_filename = 'newsletter_temp.html'
        self.rendered_filename = rendered_filename
        events = self.get_results()
        self.events_grouped = self.group_results(events)
        self.script_path = os.path.dirname(os.path.abspath(__file__))
        self.template_file_path = os.path.join(
            self.script_path, self.template_filename)
        self.rendered_file_path = os.path.join(
            self.script_path, self.rendered_filename)
        self.environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.script_path))
        self.output_text = self.environment.get_template(
            self.template_filename).render(events_grouped=self.events_grouped, dates=self.date_list)
        self.render_newsletter()

    def get_results(self):
        results_list = []
        results_col = db.Connector('results')
        for date in self.date_list:
            results = results_col.find({"date": date})
            for show in results:
                results_list.append(show)

        results_list.sort(key=lambda x: x['promotion'])

        return results_list

    def group_results(self, results_list):
        events_grouped = []
        for k, v in groupby(results_list, key=lambda x: x['promotion']):
            prom_events = {}
            prom_events['promotion'] = k
            prom_events['events'] = list(v)
            events_grouped.append(prom_events)
        return events_grouped

    def render_newsletter(self):
        with open(self.rendered_file_path, "w") as result_file:
            result_file.write(self.output_text)


if __name__ == "__main__":

    rendered_filename = 'puroview_newsletter_{}_week{}.html'.format(datetime.today().year,
                                                                    datetime.today().strftime("%V"))

    newsletter = Newsletter(rendered_filename)

    storage = Storage('puroview-static', rendered_filename,
                      'newsletters/' + rendered_filename)

    newsletter_url = storage.upload_file()
    print('Uploaded Newsletter: ' + newsletter_url)
    newsletter_info = {
        "url": newsletter_url,
        "year": str(datetime.today().year),
        "week": datetime.today().strftime("%V"),
        "firstdate": newsletter.date_list[0],
        "lastdate": newsletter.date_list[6]
    }
    db = db.Connector('newsletters')
    db.update({"url": newsletter_info["url"]}, newsletter_info)

    notifier = notifier.Notifier()
    notifier.pushover("New Newsletter Created! URL: " + newsletter_url)

    print(newsletter_info)
