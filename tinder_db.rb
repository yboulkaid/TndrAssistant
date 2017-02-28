require 'sequel'
require 'virtus'

DB = Sequel.connect('mysql://root:@127.0.0.1/tndr_assistant')
DB[:TndrAssistant]

class User
  include Virtus.model
  attribute :user_id
  attribute :name
  attribute :liked
  attribute :content_hash
  attribute :s_number

  def self.not_liked
    DB[:TndrAssistant].where(liked: nil).map { |record| self.new(record) }
  end

  def self.liked
    DB[:TndrAssistant].where(liked: 1).map { |record| self.new(record) }
  end

  def self.fetch!
    3.times do
      puts `python TndrAssistant.py --store`
    end
  end

  def self.like_all_unliked
    not_liked.each(&:like!)
  end

  def self.fetch_and_like
    fetch!
    like_all_unliked
  end

  def like!
    puts "Liking user #{user_id} with like_key #{like_key}"
    `python TndrAssistant.py --like #{like_key}`
  end

  def like_key
    "#{user_id}_#{content_hash}_#{s_number}"
  end
end

class Stats
  def self.print
    puts "Liked users in db: #{User.liked.count} \n"
    puts "Not liked users in db: #{User.not_liked.count} \n"
  end

end

if ENV['TINDER_INTERACTIVE']
  binding.pry
else
  User.fetch_and_like
end
