# frozen_string_literal: true

Jekyll::Hooks.register :site, :post_read do |site|
  site.posts.docs.each do |post|
    if post.data["author"].is_a?(String)
      post.data["authors"] = [post.data.delete("author")]
    end

    post.data["last_modified_at"] ||= post.data["modified_time"]

    tags = post.data["tags"]
    tags = tags.split if tags.is_a?(String)

    next unless tags.is_a?(Array)

    post.data["tags"] = tags.map do |tag|
      case tag.downcase
      when "c++" then "cpp"
      when "c#" then "csharp"
      else tag.downcase.tr(" ", "-")
      end
    end.uniq
  end
end
